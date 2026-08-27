from __future__ import annotations

import json
from statistics import mean

from diagsql.measurement import Measurement
from diagsql.model import Assumption, AssumptionGraph, Conflict, diagnosis_key
from diagsql.repair import build_repair_plan
from diagsql.simulator import ControlledEpisode, ControlledMeasurement, run_active_diagnosis


def _binary_episode(
    *,
    fault_a: str,
    fault_b: str,
    hidden_fault: str,
    measurement_id: str,
    positive_outcome: str,
    negative_outcome: str,
    cost: float,
    extra_assumptions: tuple[Assumption, ...],
) -> ControlledEpisode:
    graph = AssumptionGraph(
        [
            Assumption(fault_a, fault_a, f"semantic assumption {fault_a}"),
            Assumption(fault_b, fault_b, f"semantic assumption {fault_b}"),
            *extra_assumptions,
        ]
    )
    initial_conflict = Conflict(frozenset({fault_a, fault_b}), f"initial:{fault_a}:{fault_b}")
    measurement = Measurement(
        measurement_id,
        cost=cost,
        outcome_likelihoods={
            positive_outcome: {
                (fault_a,): 1.0,
                (fault_b,): 0.0,
            },
            negative_outcome: {
                (fault_a,): 0.0,
                (fault_b,): 1.0,
            },
        },
    )
    controlled = ControlledMeasurement(
        measurement=measurement,
        actual_outcome_by_fault={
            (fault_a,): positive_outcome,
            (fault_b,): negative_outcome,
        },
        conflicts_by_outcome={
            positive_outcome: (
                Conflict(frozenset({fault_a}), f"evidence:{measurement_id}:{positive_outcome}"),
            ),
            negative_outcome: (
                Conflict(frozenset({fault_b}), f"evidence:{measurement_id}:{negative_outcome}"),
            ),
        },
    )
    return ControlledEpisode(
        graph=graph,
        hidden_faults=frozenset({hidden_fault}),
        initial_conflicts=(initial_conflict,),
        measurements=(controlled,),
    )


def build_episodes() -> list[tuple[str, ControlledEpisode]]:
    metric_join = _binary_episode(
        fault_a="metric",
        fault_b="join",
        hidden_fault="metric",
        measurement_id="metric_definition_lookup",
        positive_outcome="metric_mismatch",
        negative_outcome="join_mismatch",
        cost=0.6,
        extra_assumptions=(
            Assumption("amount", "schema", "orders.amount source", dependencies=("metric",)),
            Assumption("refund", "filter", "refund handling", dependencies=("amount",)),
            Assumption("join_key", "schema", "customer join key", dependencies=("join",)),
            Assumption("region", "schema", "region dimension"),
        ),
    )
    time_filter = _binary_episode(
        fault_a="time",
        fault_b="filter",
        hidden_fault="time",
        measurement_id="calendar_rule_lookup",
        positive_outcome="time_mismatch",
        negative_outcome="filter_mismatch",
        cost=0.4,
        extra_assumptions=(
            Assumption("date_field", "schema", "date field", dependencies=("time",)),
            Assumption("status_value", "value_mapping", "status mapping", dependencies=("filter",)),
            Assumption("entity", "entity", "customer entity"),
            Assumption("region", "schema", "region dimension"),
        ),
    )
    grain_dedup = _binary_episode(
        fault_a="grain",
        fault_b="dedup",
        hidden_fault="grain",
        measurement_id="row_cardinality_probe",
        positive_outcome="grain_mismatch",
        negative_outcome="dedup_mismatch",
        cost=0.3,
        extra_assumptions=(
            Assumption("group_by", "sql", "grouping clause", dependencies=("grain",)),
            Assumption("distinct_key", "sql", "distinct key", dependencies=("dedup",)),
            Assumption("time", "time", "comparison window"),
            Assumption("region", "schema", "region dimension"),
        ),
    )
    return [
        ("metric_vs_join", metric_join),
        ("time_vs_filter", time_filter),
        ("grain_vs_dedup", grain_dedup),
    ]


def run_benchmark() -> dict[str, object]:
    episode_reports: list[dict[str, object]] = []
    fixed_correct = 0
    active_correct = 0
    costs: list[float] = []
    repair_scope_fractions: list[float] = []

    for name, episode in build_episodes():
        trace = run_active_diagnosis(episode)
        initial_top = trace.initial_diagnoses[0]
        final_top = trace.final_diagnoses[0]
        hidden_key = diagnosis_key(episode.hidden_faults)
        initial_key = diagnosis_key(initial_top)
        final_key = diagnosis_key(final_top)
        fixed_hit = initial_key == hidden_key
        active_hit = final_key == hidden_key
        fixed_correct += int(fixed_hit)
        active_correct += int(active_hit)
        costs.append(trace.total_cost)

        repair_plan = build_repair_plan(episode.graph, final_top)
        scope_fraction = len(repair_plan.editable_ids) / len(episode.graph.assumptions)
        repair_scope_fractions.append(scope_fraction)

        episode_reports.append(
            {
                "name": name,
                "hidden_faults": list(hidden_key),
                "initial_top_diagnosis": list(initial_key),
                "final_top_diagnosis": list(final_key),
                "fixed_diagnosis_correct": fixed_hit,
                "diagnosis_correct": active_hit,
                "measurements": list(trace.measurement_ids),
                "outcomes": list(trace.outcomes),
                "measurement_cost": trace.total_cost,
                "repair_mode": repair_plan.mode,
                "repair_scope_size": len(repair_plan.editable_ids),
                "repair_scope_fraction": round(scope_fraction, 4),
            }
        )

    n = len(episode_reports)
    return {
        "aggregate": {
            "episodes": n,
            "fixed_top1_diagnosis_accuracy": fixed_correct / n,
            "active_top1_diagnosis_accuracy": active_correct / n,
            "mean_measurement_cost": round(mean(costs), 4),
            "mean_repair_scope_fraction": round(mean(repair_scope_fractions), 4),
        },
        "episodes": episode_reports,
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2, sort_keys=True))
