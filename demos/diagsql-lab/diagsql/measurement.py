from __future__ import annotations

from dataclasses import dataclass
from math import exp, log2
from typing import Mapping, Sequence

from .model import Diagnosis, diagnosis_key


@dataclass(frozen=True)
class Measurement:
    id: str
    cost: float
    outcome_likelihoods: Mapping[str, Mapping[tuple[str, ...], float]]

    def __post_init__(self) -> None:
        if self.cost < 0:
            raise ValueError("measurement cost must be non-negative")


@dataclass(frozen=True)
class MeasurementChoice:
    measurement: Measurement
    information_gain: float
    utility: float


def _entropy(probabilities: Sequence[float]) -> float:
    return -sum(p * log2(p) for p in probabilities if p > 0)


def normalize_diagnosis_probabilities(diagnoses: Sequence[Diagnosis]) -> list[float]:
    if not diagnoses:
        return []
    weights = [exp(-item.score) for item in diagnoses]
    total = sum(weights)
    return [weight / total for weight in weights]


def _validate_likelihoods(measurement: Measurement, diagnoses: Sequence[Diagnosis]) -> None:
    for diagnosis in diagnoses:
        key = diagnosis_key(diagnosis)
        values = [mapping.get(key, 0.0) for mapping in measurement.outcome_likelihoods.values()]
        if any(value < 0 or value > 1 for value in values):
            raise ValueError("outcome likelihoods must be in [0, 1]")
        if abs(sum(values) - 1.0) > 1e-6:
            raise ValueError(f"outcome likelihoods for {key} must sum to 1")


def expected_information_gain(
    measurement: Measurement,
    diagnoses: Sequence[Diagnosis],
    probabilities: Sequence[float],
) -> float:
    if len(diagnoses) != len(probabilities):
        raise ValueError("diagnoses and probabilities must have equal length")
    _validate_likelihoods(measurement, diagnoses)
    prior_entropy = _entropy(probabilities)
    expected_posterior_entropy = 0.0
    for mapping in measurement.outcome_likelihoods.values():
        joint = [
            probabilities[i] * mapping.get(diagnosis_key(diagnosis), 0.0)
            for i, diagnosis in enumerate(diagnoses)
        ]
        outcome_probability = sum(joint)
        if outcome_probability <= 0:
            continue
        posterior = [value / outcome_probability for value in joint]
        expected_posterior_entropy += outcome_probability * _entropy(posterior)
    return prior_entropy - expected_posterior_entropy


def choose_measurement(
    measurements: Sequence[Measurement],
    diagnoses: Sequence[Diagnosis],
    probabilities: Sequence[float] | None = None,
    lambda_cost: float = 0.25,
) -> MeasurementChoice:
    if not measurements:
        raise ValueError("at least one measurement is required")
    probs = list(probabilities) if probabilities is not None else normalize_diagnosis_probabilities(diagnoses)
    choices: list[MeasurementChoice] = []
    for measurement in measurements:
        gain = expected_information_gain(measurement, diagnoses, probs)
        utility = gain - lambda_cost * measurement.cost
        choices.append(MeasurementChoice(measurement, gain, utility))
    return max(choices, key=lambda item: (item.utility, -item.measurement.cost, item.measurement.id))
