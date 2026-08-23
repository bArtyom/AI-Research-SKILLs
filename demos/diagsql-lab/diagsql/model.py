from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Assumption:
    id: str
    type: str
    claim: str
    confidence: float = 0.5
    dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True)
class Conflict:
    assumption_ids: frozenset[str]
    evidence_id: str
    hard: bool = True
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.assumption_ids:
            raise ValueError("conflict requires at least one assumption")
        if self.weight < 0:
            raise ValueError("conflict weight must be non-negative")


@dataclass(frozen=True)
class Diagnosis:
    faulty_ids: frozenset[str]
    score: float


def diagnosis_key(diagnosis: Diagnosis | frozenset[str]) -> tuple[str, ...]:
    ids = diagnosis.faulty_ids if isinstance(diagnosis, Diagnosis) else diagnosis
    return tuple(sorted(ids))


class AssumptionGraph:
    def __init__(self, assumptions: Iterable[Assumption]):
        items = list(assumptions)
        self.assumptions = {item.id: item for item in items}
        if len(self.assumptions) != len(items):
            raise ValueError("assumption ids must be unique")
        for item in items:
            for parent in item.dependencies:
                if parent not in self.assumptions:
                    raise ValueError(f"unknown dependency: {parent}")

    def descendants(self, roots: set[str] | frozenset[str]) -> set[str]:
        children: dict[str, set[str]] = {key: set() for key in self.assumptions}
        for item in self.assumptions.values():
            for parent in item.dependencies:
                children[parent].add(item.id)
        seen: set[str] = set()
        frontier = list(roots)
        while frontier:
            current = frontier.pop()
            for child in children.get(current, set()):
                if child not in seen and child not in roots:
                    seen.add(child)
                    frontier.append(child)
        return seen
