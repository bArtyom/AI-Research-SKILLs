from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .diagnosis import rank_diagnoses
from .measurement import Measurement, choose_measurement, normalize_diagnosis_probabilities
from .model import AssumptionGraph, Conflict, Diagnosis, diagnosis_key


@dataclass(frozen=True)
class ControlledMeasurement:
    measurement: Measurement
    actual_outcome_by_fault: Mapping[tuple[str, ...], str]
    conflicts_by_outcome: Mapping[str, tuple[Conflict, ...]]


@dataclass(frozen=True)
class ControlledEpisode:
    graph: AssumptionGraph
    hidden_faults: frozenset[str]
    initial_conflicts: tuple[Conflict, ...]
    measurements: tuple[ControlledMeasurement, ...]


@dataclass(frozen=True)
class DiagnosticTrace:
    initial_diagnoses: tuple[Diagnosis, ...]
    final_diagnoses: tuple[Diagnosis, ...]
    measurement_ids: tuple[str, ...]
    outcomes: tuple[str, ...]
    total_cost: float
    conflict_count: int


def _measurement_covers(measurement: Measurement, diagnoses: list[Diagnosis]) -> bool:
    for diagnosis in diagnoses:
        key = diagnosis_key(diagnosis)
        total = sum(mapping.get(key, 0.0) for mapping in measurement.outcome_likelihoods.values())
        if abs(total - 1.0) > 1e-6:
            return False
    return True


def run_active_diagnosis(
    episode: ControlledEpisode,
    max_steps: int = 4,
    lambda_cost: float = 0.25,
) -> DiagnosticTrace:
    conflicts = list(episode.initial_conflicts)
    diagnoses = rank_diagnoses(episode.graph, conflicts)
    if not diagnoses:
        raise ValueError("initial conflicts produced no diagnosis")
    initial_diagnoses = tuple(diagnoses)
    used: set[str] = set()
    measurement_ids: list[str] = []
    outcomes: list[str] = []
    total_cost = 0.0
    hidden_key = diagnosis_key(episode.hidden_faults)

    for _ in range(max_steps):
        if len(diagnoses) <= 1:
            break

        eligible = [
            controlled
            for controlled in episode.measurements
            if controlled.measurement.id not in used
            and hidden_key in controlled.actual_outcome_by_fault
            and _measurement_covers(controlled.measurement, diagnoses)
        ]
        if not eligible:
            break

        probabilities = normalize_diagnosis_probabilities(diagnoses)
        choice = choose_measurement(
            [controlled.measurement for controlled in eligible],
            diagnoses,
            probabilities,
            lambda_cost=lambda_cost,
        )
        controlled = next(
            item for item in eligible if item.measurement.id == choice.measurement.id
        )
        outcome = controlled.actual_outcome_by_fault[hidden_key]
        if outcome not in controlled.conflicts_by_outcome:
            raise ValueError(
                f"measurement {controlled.measurement.id} has no conflicts for outcome {outcome}"
            )

        used.add(controlled.measurement.id)
        measurement_ids.append(controlled.measurement.id)
        outcomes.append(outcome)
        total_cost += controlled.measurement.cost
        conflicts.extend(controlled.conflicts_by_outcome[outcome])
        diagnoses = rank_diagnoses(episode.graph, conflicts)
        if not diagnoses:
            raise ValueError("measurement conflicts eliminated all diagnoses")

    return DiagnosticTrace(
        initial_diagnoses=initial_diagnoses,
        final_diagnoses=tuple(diagnoses),
        measurement_ids=tuple(measurement_ids),
        outcomes=tuple(outcomes),
        total_cost=total_cost,
        conflict_count=len(conflicts),
    )
