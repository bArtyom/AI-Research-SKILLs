from __future__ import annotations

from dataclasses import dataclass
import json
import random
import sqlite3
from statistics import mean

from aida_lab import AIDAAgent, AdaptivePolicy, SQLiteWorld
from benchmark import NoClarificationPolicy, oracle_semantic_score


@dataclass(frozen=True)
class Scenario:
    seed: int
    expected_metric: str
    question: str
    previous: dict[str, tuple[float, int]]
    current: dict[str, tuple[float, int]]
    cancelled_outlier: tuple[str, float]


def generate_scenario(seed: int) -> Scenario:
    rng = random.Random(seed)
    regions = ["East", "West", "North", "South"]
    expected_metric = rng.choice(["revenue", "order_count"])

    previous: dict[str, tuple[float, int]] = {}
    current: dict[str, tuple[float, int]] = {}
    for region in regions:
        prev_orders = rng.randint(2, 6)
        curr_orders = rng.randint(2, 7)
        prev_revenue = round(prev_orders * rng.uniform(60, 180), 2)
        curr_revenue = round(curr_orders * rng.uniform(60, 220), 2)
        previous[region] = (prev_revenue, prev_orders)
        current[region] = (curr_revenue, curr_orders)

    cancelled_outlier = (rng.choice(regions), round(rng.uniform(5000, 15000), 2))
    return Scenario(
        seed=seed,
        expected_metric=expected_metric,
        question="Which regions grew fastest last quarter?",
        previous=previous,
        current=current,
        cancelled_outlier=cancelled_outlier,
    )


def scenario_db(scenario: Scenario) -> sqlite3.Connection:
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
        """
    )

    regions = list(scenario.previous)
    customer_ids = {}
    for idx, region in enumerate(regions, start=1):
        customer_ids[region] = idx
        conn.execute(
            "INSERT INTO customers VALUES (?, ?, 'active', '2025-01-01')",
            (idx, region),
        )

    order_id = 1
    for period_date, values in [
        ("2026-02-10", scenario.previous),
        ("2026-05-10", scenario.current),
    ]:
        for region, (revenue, order_count) in values.items():
            per_order = revenue / order_count
            for _ in range(order_count):
                conn.execute(
                    "INSERT INTO orders VALUES (?, ?, ?, 'completed', ?)",
                    (order_id, customer_ids[region], per_order, period_date),
                )
                order_id += 1

    outlier_region, outlier_amount = scenario.cancelled_outlier
    conn.execute(
        "INSERT INTO orders VALUES (?, ?, ?, 'cancelled', '2026-05-11')",
        (order_id, customer_ids[outlier_region], outlier_amount),
    )
    conn.commit()
    return conn


def run_episode(scenario: Scenario, policy, name: str) -> dict:
    agent = AIDAAgent(
        SQLiteWorld(scenario_db(scenario)),
        policy=policy,
        user_answerer=lambda key, default: scenario.expected_metric if key == "metric" else default,
    )
    state, ledger = agent.run(scenario.question)
    return {
        "seed": scenario.seed,
        "policy": name,
        "expected_metric": scenario.expected_metric,
        "semantic_success": oracle_semantic_score(state, scenario.expected_metric),
        "internal_verifier": state.verifier_score,
        "cost": ledger.estimated_cost,
        "tool_calls": ledger.tool_calls,
        "user_interruptions": ledger.user_interruptions,
    }


def benchmark_gym(episodes: int = 50) -> dict:
    rows = []
    for seed in range(episodes):
        scenario = generate_scenario(seed)
        rows.append(run_episode(scenario, NoClarificationPolicy(), "fixed-no-clarification"))
        rows.append(run_episode(scenario, AdaptivePolicy(), "adaptive-uncertainty-aware"))

    summary = {}
    for policy in sorted({r["policy"] for r in rows}):
        subset = [r for r in rows if r["policy"] == policy]
        summary[policy] = {
            "episodes": len(subset),
            "semantic_success_rate": round(mean(r["semantic_success"] for r in subset), 3),
            "internal_verifier_mean": round(mean(r["internal_verifier"] for r in subset), 3),
            "mean_cost": round(mean(r["cost"] for r in subset), 3),
            "mean_tool_calls": round(mean(r["tool_calls"] for r in subset), 3),
            "mean_user_interruptions": round(mean(r["user_interruptions"] for r in subset), 3),
        }
    return {"summary": summary, "episodes": rows}


if __name__ == "__main__":
    result = benchmark_gym(episodes=50)
    print(json.dumps(result["summary"], indent=2))
