from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
import json
import sqlite3
import time


class Action(str, Enum):
    INSPECT_SCHEMA = "inspect_schema"
    SAMPLE_VALUES = "sample_values"
    ASK_USER = "ask_user"
    GENERATE_SQL = "generate_sql"
    EXECUTE_SQL = "execute_sql"
    EXPLAIN_SQL = "explain_sql"
    VERIFY = "verify"
    STOP = "stop"


@dataclass
class CostLedger:
    tool_calls: int = 0
    db_calls: int = 0
    user_interruptions: int = 0
    estimated_cost: float = 0.0
    wall_time_s: float = 0.0


@dataclass
class BeliefState:
    question: str
    schema_uncertainty: float = 0.8
    semantic_uncertainty: float = 0.8
    execution_uncertainty: float = 1.0
    safety_risk: float = 0.0
    schema: dict[str, list[str]] = field(default_factory=dict)
    samples: dict[str, list[tuple[Any, ...]]] = field(default_factory=dict)
    clarified_facts: dict[str, str] = field(default_factory=dict)
    candidate_sql: str | None = None
    result: list[tuple[Any, ...]] | None = None
    explain: list[tuple[Any, ...]] | None = None
    verifier_score: float = 0.0
    verifier_notes: list[str] = field(default_factory=list)
    trajectory: list[dict[str, Any]] = field(default_factory=list)

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_uncertainty": round(self.schema_uncertainty, 3),
            "semantic_uncertainty": round(self.semantic_uncertainty, 3),
            "execution_uncertainty": round(self.execution_uncertainty, 3),
            "safety_risk": round(self.safety_risk, 3),
            "has_schema": bool(self.schema),
            "clarified_facts": dict(self.clarified_facts),
            "candidate_sql": self.candidate_sql,
            "verifier_score": round(self.verifier_score, 3),
        }


class SQLiteWorld:
    """A deliberately small database world for agent-policy experiments."""

    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    def inspect_schema(self) -> dict[str, list[str]]:
        tables = [r[0] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )]
        schema: dict[str, list[str]] = {}
        for table in tables:
            schema[table] = [r[1] for r in self.conn.execute(f"PRAGMA table_info('{table}')")]
        return schema

    def sample_values(self, table: str, limit: int = 3) -> list[tuple[Any, ...]]:
        safe_table = table.replace("'", "''")
        return list(self.conn.execute(f"SELECT * FROM '{safe_table}' LIMIT ?", (limit,)))

    def execute(self, sql: str) -> list[tuple[Any, ...]]:
        if not sql.lstrip().lower().startswith(("select", "with", "explain")):
            raise ValueError("Demo sandbox only permits read-only SQL")
        return list(self.conn.execute(sql))

    def explain(self, sql: str) -> list[tuple[Any, ...]]:
        return list(self.conn.execute("EXPLAIN QUERY PLAN " + sql))


class ToyReasoner:
    """Replaceable stand-in for an LLM.

    The point of the demo is the orchestration policy, not model quality. A real
    implementation can replace these methods with an LLM, code model, or
    learned policy without changing the environment contract.
    """

    def clarification_question(self, state: BeliefState) -> tuple[str, str, str]:
        q = state.question.lower()
        if "grow" in q or "growth" in q:
            return (
                "metric",
                "When you say growth, should I use revenue or order count?",
                "revenue",
            )
        return ("metric", "Which business metric should define the ranking?", "revenue")

    def generate_sql(self, state: BeliefState) -> str:
        metric = state.clarified_facts.get("metric", "order_count")
        if metric == "revenue":
            value_expr = "SUM(o.amount)"
        else:
            value_expr = "COUNT(*)"

        # The demo uses two adjacent 90-day windows to keep the SQL portable.
        return f"""
WITH bucketed AS (
    SELECT c.region,
           CASE WHEN o.order_date >= '2026-04-01' THEN 'current' ELSE 'previous' END AS period,
           {value_expr} AS value
    FROM orders o
    JOIN customers c ON c.id = o.customer_id
    WHERE o.order_date >= '2026-01-01' AND o.order_date < '2026-07-01'
      AND o.status = 'completed'
    GROUP BY c.region, period
), pivot AS (
    SELECT region,
           SUM(CASE WHEN period='current' THEN value ELSE 0 END) AS current_value,
           SUM(CASE WHEN period='previous' THEN value ELSE 0 END) AS previous_value
    FROM bucketed
    GROUP BY region
)
SELECT region,
       ROUND((current_value - previous_value) / NULLIF(previous_value, 0.0), 4) AS growth
FROM pivot
ORDER BY growth DESC;
""".strip()


class VerifierBank:
    """Deterministic checks that can be extended with learned verifiers."""

    def verify(self, state: BeliefState) -> tuple[float, list[str]]:
        notes: list[str] = []
        score = 1.0
        sql = (state.candidate_sql or "").lower()

        if state.result is None:
            return 0.0, ["SQL has not been executed"]
        if not state.result:
            score -= 0.25
            notes.append("empty result")
        if "join customers" not in sql:
            score -= 0.25
            notes.append("region requires customer join")
        if state.clarified_facts.get("metric") == "revenue" and "sum(o.amount)" not in sql:
            score -= 0.35
            notes.append("clarified metric is revenue but query does not sum amount")
        if "nullif" not in sql:
            score -= 0.10
            notes.append("growth denominator is not protected against zero")
        if state.explain is None:
            score -= 0.05
            notes.append("query plan not inspected")

        return max(score, 0.0), notes or ["all deterministic checks passed"]


class AdaptivePolicy:
    """A simple uncertainty-aware policy used as a baseline.

    This is intentionally transparent. It can later be replaced by a learned
    contextual bandit, policy-gradient agent, or value-of-information planner.
    """

    def choose(self, state: BeliefState) -> Action:
        if state.schema_uncertainty > 0.45:
            return Action.INSPECT_SCHEMA
        if state.semantic_uncertainty > 0.45:
            return Action.ASK_USER
        if state.candidate_sql is None:
            return Action.GENERATE_SQL
        if state.result is None:
            return Action.EXECUTE_SQL
        if state.explain is None:
            return Action.EXPLAIN_SQL
        if state.verifier_score < 0.90:
            return Action.VERIFY
        return Action.STOP


@dataclass
class AgentConfig:
    max_steps: int = 12
    max_estimated_cost: float = 10.0
    action_costs: dict[Action, float] = field(default_factory=lambda: {
        Action.INSPECT_SCHEMA: 0.25,
        Action.SAMPLE_VALUES: 0.35,
        Action.ASK_USER: 2.0,
        Action.GENERATE_SQL: 1.0,
        Action.EXECUTE_SQL: 0.5,
        Action.EXPLAIN_SQL: 0.3,
        Action.VERIFY: 0.6,
        Action.STOP: 0.0,
    })


class AIDAAgent:
    def __init__(
        self,
        world: SQLiteWorld,
        reasoner: ToyReasoner | None = None,
        verifier: VerifierBank | None = None,
        policy: AdaptivePolicy | None = None,
        config: AgentConfig | None = None,
        user_answerer: Callable[[str, str], str] | None = None,
    ) -> None:
        self.world = world
        self.reasoner = reasoner or ToyReasoner()
        self.verifier = verifier or VerifierBank()
        self.policy = policy or AdaptivePolicy()
        self.config = config or AgentConfig()
        self.user_answerer = user_answerer or (lambda _key, default: default)

    def run(self, question: str) -> tuple[BeliefState, CostLedger]:
        state = BeliefState(question=question)
        ledger = CostLedger()
        started = time.perf_counter()

        for step in range(self.config.max_steps):
            action = self.policy.choose(state)
            action_cost = self.config.action_costs[action]
            if ledger.estimated_cost + action_cost > self.config.max_estimated_cost:
                state.trajectory.append({"step": step, "action": "budget_stop", "state": state.snapshot()})
                break

            ledger.tool_calls += int(action != Action.STOP)
            ledger.estimated_cost += action_cost
            before = state.snapshot()

            if action == Action.INSPECT_SCHEMA:
                state.schema = self.world.inspect_schema()
                state.schema_uncertainty = 0.15
                ledger.db_calls += 1
            elif action == Action.ASK_USER:
                key, prompt, default = self.reasoner.clarification_question(state)
                state.clarified_facts[key] = self.user_answerer(key, default)
                state.semantic_uncertainty = 0.15
                ledger.user_interruptions += 1
                state.verifier_score = 0.0
            elif action == Action.GENERATE_SQL:
                state.candidate_sql = self.reasoner.generate_sql(state)
                state.execution_uncertainty = 0.75
                state.result = None
                state.explain = None
                state.verifier_score = 0.0
            elif action == Action.EXECUTE_SQL:
                state.result = self.world.execute(state.candidate_sql or "")
                state.execution_uncertainty = 0.25
                ledger.db_calls += 1
            elif action == Action.EXPLAIN_SQL:
                state.explain = self.world.explain(state.candidate_sql or "")
                ledger.db_calls += 1
            elif action == Action.VERIFY:
                state.verifier_score, state.verifier_notes = self.verifier.verify(state)
                state.execution_uncertainty = max(0.05, 1.0 - state.verifier_score)
            elif action == Action.STOP:
                state.trajectory.append({"step": step, "action": action.value, "before": before, "after": state.snapshot()})
                break
            else:
                raise NotImplementedError(action)

            state.trajectory.append({"step": step, "action": action.value, "before": before, "after": state.snapshot()})

        ledger.wall_time_s = time.perf_counter() - started
        return state, ledger


def create_demo_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE customers(
            id INTEGER PRIMARY KEY,
            region TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE orders(
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        );
        INSERT INTO customers VALUES
            (1, 'East', 'active', '2025-01-01'),
            (2, 'West', 'active', '2025-01-02'),
            (3, 'North', 'active', '2025-01-03');
        INSERT INTO orders VALUES
            (1, 1, 100, 'completed', '2026-02-10'),
            (2, 2, 200, 'completed', '2026-02-10'),
            (3, 3, 150, 'completed', '2026-02-10'),
            (4, 1, 160, 'completed', '2026-05-10'),
            (5, 2, 250, 'completed', '2026-05-10'),
            (6, 3, 300, 'completed', '2026-05-10'),
            (7, 3, 999, 'cancelled', '2026-05-11');
        """
    )
    return conn


def demo() -> dict[str, Any]:
    world = SQLiteWorld(create_demo_db())
    agent = AIDAAgent(world)
    state, ledger = agent.run("Which regions grew fastest last quarter?")
    return {
        "final_state": state.snapshot(),
        "result": state.result,
        "verifier_notes": state.verifier_notes,
        "ledger": ledger.__dict__,
        "trajectory": state.trajectory,
    }


if __name__ == "__main__":
    print(json.dumps(demo(), indent=2, default=str))
