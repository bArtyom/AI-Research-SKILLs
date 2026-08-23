from __future__ import annotations

from itertools import combinations
from math import log
from typing import Mapping, Sequence

from .model import AssumptionGraph, Conflict, Diagnosis


def minimal_hitting_sets(
    conflicts: Sequence[Conflict],
    max_cardinality: int = 3,
    limit: int = 20,
) -> list[frozenset[str]]:
    hard_sets = [set(c.assumption_ids) for c in conflicts if c.hard]
    if not hard_sets:
        return [frozenset()]
    universe = sorted(set().union(*hard_sets))
    results: list[frozenset[str]] = []
    for size in range(1, min(max_cardinality, len(universe)) + 1):
        for combo in combinations(universe, size):
            candidate = frozenset(combo)
            if any(existing < candidate for existing in results):
                continue
            if all(candidate.intersection(conflict) for conflict in hard_sets):
                results.append(candidate)
                if len(results) >= limit:
                    return results
    return results


def rank_diagnoses(
    graph: AssumptionGraph,
    conflicts: Sequence[Conflict],
    fault_priors: Mapping[str, float] | None = None,
    max_cardinality: int = 3,
    limit: int = 20,
    cardinality_penalty: float = 0.1,
    soft_penalty: float = 1.0,
) -> list[Diagnosis]:
    priors = dict(fault_priors or {})
    candidates = minimal_hitting_sets(conflicts, max_cardinality=max_cardinality, limit=limit)
    ranked: list[Diagnosis] = []
    for candidate in candidates:
        for assumption_id in candidate:
            if assumption_id not in graph.assumptions:
                raise ValueError(f"unknown assumption in diagnosis: {assumption_id}")
        prior_cost = 0.0
        for assumption_id in candidate:
            p = min(max(priors.get(assumption_id, 0.1), 1e-6), 1.0)
            prior_cost += -log(p)
        missed_soft = sum(
            conflict.weight
            for conflict in conflicts
            if not conflict.hard and candidate.isdisjoint(conflict.assumption_ids)
        )
        score = prior_cost + cardinality_penalty * len(candidate) + soft_penalty * missed_soft
        ranked.append(Diagnosis(candidate, score))
    ranked.sort(key=lambda item: (item.score, len(item.faulty_ids), sorted(item.faulty_ids)))
    return ranked
