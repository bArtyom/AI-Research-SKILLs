from __future__ import annotations

from dataclasses import dataclass

from .model import AssumptionGraph, Diagnosis


@dataclass(frozen=True)
class RepairPlan:
    diagnosis: Diagnosis
    editable_ids: frozenset[str]
    mode: str


def build_repair_plan(
    graph: AssumptionGraph,
    diagnosis: Diagnosis,
    global_threshold: float = 0.6,
) -> RepairPlan:
    if not 0.0 < global_threshold <= 1.0:
        raise ValueError("global_threshold must be in (0, 1]")
    unknown = set(diagnosis.faulty_ids).difference(graph.assumptions)
    if unknown:
        raise ValueError(f"unknown assumptions in diagnosis: {sorted(unknown)}")
    editable = set(diagnosis.faulty_ids)
    editable.update(graph.descendants(diagnosis.faulty_ids))
    ratio = len(editable) / max(len(graph.assumptions), 1)
    if ratio <= 0.30:
        mode = "patch"
    elif ratio <= global_threshold:
        mode = "local_regenerate"
    else:
        mode = "global_regenerate"
    return RepairPlan(diagnosis, frozenset(editable), mode)
