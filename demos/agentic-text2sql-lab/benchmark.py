from __future__ import annotations

import json
from aida_lab import Action, AIDAAgent, AdaptivePolicy, SQLiteWorld, create_demo_db


class NoClarificationPolicy:
    """A fixed pipeline that never asks the user, even when intent is ambiguous."""

    sequence = [
        Action.INSPECT_SCHEMA,
        Action.GENERATE_SQL,
        Action.EXECUTE_SQL,
        Action.EXPLAIN_SQL,
        Action.VERIFY,
        Action.STOP,
    ]

    def choose(self, state):
        idx = len(state.trajectory)
        return self.sequence[min(idx, len(self.sequence) - 1)]


def oracle_semantic_score(state, expected_metric: str = "revenue") -> float:
    """Hidden evaluation oracle used only for the toy benchmark.

    This intentionally differs from the agent's internal verifier. The gap
    illustrates a core research problem: executable and locally verified SQL
    can still be semantically wrong when the user's intent was never resolved.
    """

    sql = (state.candidate_sql or "").lower()
    if expected_metric == "revenue":
        return float("sum(o.amount)" in sql)
    if expected_metric == "order_count":
        return float("count(*)" in sql)
    return 0.0


def run(policy, name: str) -> dict:
    agent = AIDAAgent(SQLiteWorld(create_demo_db()), policy=policy)
    state, ledger = agent.run("Which regions grew fastest last quarter?")
    return {
        "policy": name,
        "internal_verifier": state.verifier_score,
        "hidden_semantic_oracle": oracle_semantic_score(state),
        "tool_calls": ledger.tool_calls,
        "db_calls": ledger.db_calls,
        "user_interruptions": ledger.user_interruptions,
        "estimated_cost": ledger.estimated_cost,
        "top_result": state.result[0] if state.result else None,
        "actions": [x["action"] for x in state.trajectory],
    }


if __name__ == "__main__":
    results = [
        run(NoClarificationPolicy(), "fixed-no-clarification"),
        run(AdaptivePolicy(), "adaptive-uncertainty-aware"),
    ]
    print(json.dumps(results, indent=2, default=str))
