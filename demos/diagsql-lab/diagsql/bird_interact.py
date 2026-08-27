from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class BirdAmbiguityLabel:
    label_id: str
    term: str
    ambiguity_type: str
    masked: bool
    critical: bool
    source: str
    sql_snippet: str | None = None
    deleted_knowledge: int | str | None = None


@dataclass(frozen=True)
class BirdInteractRecord:
    instance_id: str
    selected_database: str
    ambiguous_query: str
    category: str | None
    high_level: bool | None
    critical_ambiguities: tuple[BirdAmbiguityLabel, ...]
    noncritical_ambiguities: tuple[BirdAmbiguityLabel, ...]
    knowledge_ambiguities: tuple[BirdAmbiguityLabel, ...]
    evaluator_query: str | None = None
    has_gold_sql: bool = False
    has_test_cases: bool = False


@dataclass(frozen=True)
class BirdRuntimeTask:
    instance_id: str
    selected_database: str
    ambiguous_query: str
    category: str | None
    high_level: bool | None


@dataclass(frozen=True)
class MeasurementRecommendation:
    action: str
    target: str
    estimated_cost: float
    rationale: str


@dataclass(frozen=True)
class BirdDiagnosticCase:
    case_id: str
    runtime_task: BirdRuntimeTask
    oracle_label: BirdAmbiguityLabel
    fault_family: str
    hidden_faults: frozenset[str]
    recommendations: tuple[MeasurementRecommendation, ...]


@dataclass(frozen=True)
class BirdDatasetStats:
    records: int
    critical_ambiguities: int
    noncritical_ambiguities: int
    knowledge_ambiguities: int
    records_with_multiple_critical: int
    masked_ambiguities: int
    ambiguity_type_counts: dict[str, int]
    records_with_query: int
    records_with_gold_sql: int
    records_with_test_cases: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "records": self.records,
            "critical_ambiguities": self.critical_ambiguities,
            "noncritical_ambiguities": self.noncritical_ambiguities,
            "knowledge_ambiguities": self.knowledge_ambiguities,
            "records_with_multiple_critical": self.records_with_multiple_critical,
            "masked_ambiguities": self.masked_ambiguities,
            "ambiguity_type_counts": dict(sorted(self.ambiguity_type_counts.items())),
            "records_with_query": self.records_with_query,
            "records_with_gold_sql": self.records_with_gold_sql,
            "records_with_test_cases": self.records_with_test_cases,
        }


def _required_text(raw: Mapping[str, Any], field: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _parse_labels(
    values: Any,
    *,
    prefix: str,
    source: str,
    critical: bool,
    preserve_evaluator_details: bool,
) -> tuple[BirdAmbiguityLabel, ...]:
    if values is None:
        return ()
    if not isinstance(values, list):
        raise ValueError(f"{prefix} ambiguity list must be a list")
    labels: list[BirdAmbiguityLabel] = []
    for index, item in enumerate(values):
        if not isinstance(item, Mapping):
            raise ValueError(f"{prefix} ambiguity item {index} must be an object")
        term = item.get("term", "")
        ambiguity_type = item.get("type", "unknown")
        if not isinstance(term, str):
            raise ValueError(f"{prefix} ambiguity item {index} term must be a string")
        if not isinstance(ambiguity_type, str):
            raise ValueError(f"{prefix} ambiguity item {index} type must be a string")
        labels.append(
            BirdAmbiguityLabel(
                label_id=f"{prefix}:{index}",
                term=term,
                ambiguity_type=ambiguity_type,
                masked=bool(item.get("is_mask", False)),
                critical=critical,
                source=source,
                sql_snippet=(item.get("sql_snippet") if preserve_evaluator_details else None),
                deleted_knowledge=(item.get("deleted_knowledge") if preserve_evaluator_details else None),
            )
        )
    return tuple(labels)


def parse_bird_interact_record(
    raw: Mapping[str, Any],
    *,
    preserve_evaluator_details: bool = False,
) -> BirdInteractRecord:
    instance_id = _required_text(raw, "instance_id")
    selected_database = _required_text(raw, "selected_database")
    ambiguous_query = _required_text(raw, "amb_user_query")

    user_ambiguity = raw.get("user_query_ambiguity") or {}
    if not isinstance(user_ambiguity, Mapping):
        raise ValueError("user_query_ambiguity must be an object")

    critical = _parse_labels(
        user_ambiguity.get("critical_ambiguity", []),
        prefix="critical",
        source="user_query",
        critical=True,
        preserve_evaluator_details=preserve_evaluator_details,
    )
    noncritical = _parse_labels(
        user_ambiguity.get("non_critical_ambiguity", []),
        prefix="noncritical",
        source="user_query",
        critical=False,
        preserve_evaluator_details=preserve_evaluator_details,
    )
    knowledge = _parse_labels(
        raw.get("knowledge_ambiguity", []),
        prefix="knowledge",
        source="knowledge",
        critical=True,
        preserve_evaluator_details=preserve_evaluator_details,
    )

    category = raw.get("category")
    if category is not None and not isinstance(category, str):
        raise ValueError("category must be a string when present")
    high_level = raw.get("high_level")
    if high_level is not None and not isinstance(high_level, bool):
        raise ValueError("high_level must be boolean when present")

    query = raw.get("query")
    evaluator_query = query if preserve_evaluator_details and isinstance(query, str) else None
    sol_sql = raw.get("sol_sql")
    test_cases = raw.get("test_cases")
    has_gold_sql = isinstance(sol_sql, list) and len(sol_sql) > 0
    has_test_cases = isinstance(test_cases, list) and len(test_cases) > 0

    return BirdInteractRecord(
        instance_id=instance_id,
        selected_database=selected_database,
        ambiguous_query=ambiguous_query,
        category=category,
        high_level=high_level,
        critical_ambiguities=critical,
        noncritical_ambiguities=noncritical,
        knowledge_ambiguities=knowledge,
        evaluator_query=evaluator_query,
        has_gold_sql=has_gold_sql,
        has_test_cases=has_test_cases,
    )


def to_runtime_task(record: BirdInteractRecord) -> BirdRuntimeTask:
    return BirdRuntimeTask(
        instance_id=record.instance_id,
        selected_database=record.selected_database,
        ambiguous_query=record.ambiguous_query,
        category=record.category,
        high_level=record.high_level,
    )


def map_ambiguity_type(ambiguity_type: str) -> str:
    mapping = {
        "knowledge_linking_ambiguity": "business_rule",
        "knowledge_ambiguity": "business_rule",
        "schema_linking_ambiguity": "schema",
        "semantic_ambiguity": "semantic",
        "intent_ambiguity": "intent",
    }
    return mapping.get(ambiguity_type, "other")


def recommend_measurements(label: BirdAmbiguityLabel) -> tuple[MeasurementRecommendation, ...]:
    family = map_ambiguity_type(label.ambiguity_type)
    target = label.term
    if family == "business_rule":
        return (
            MeasurementRecommendation("retrieve_knowledge", target, 1.0, "business-rule ambiguity"),
            MeasurementRecommendation("ask_user", target, 2.0, "clarify unresolved business semantics"),
        )
    if family == "schema":
        return (
            MeasurementRecommendation("inspect_schema", target, 0.5, "schema-linking ambiguity"),
            MeasurementRecommendation("retrieve_column_meaning", target, 0.75, "schema-linking ambiguity"),
        )
    if family == "semantic":
        return (
            MeasurementRecommendation("ask_user", target, 2.0, "semantic ambiguity"),
            MeasurementRecommendation("run_diagnostic_sql", target, 1.0, "test data-dependent semantic alternatives"),
        )
    if family == "intent":
        return (MeasurementRecommendation("ask_user", target, 2.0, "intent ambiguity"),)
    return (MeasurementRecommendation("ask_user", target, 2.0, "unclassified ambiguity"),)


def single_fault_cases(record: BirdInteractRecord) -> tuple[BirdDiagnosticCase, ...]:
    runtime = to_runtime_task(record)
    cases: list[BirdDiagnosticCase] = []
    for label in record.critical_ambiguities:
        cases.append(
            BirdDiagnosticCase(
                case_id=f"{record.instance_id}::{label.label_id}",
                runtime_task=runtime,
                oracle_label=label,
                fault_family=map_ambiguity_type(label.ambiguity_type),
                hidden_faults=frozenset({label.label_id}),
                recommendations=recommend_measurements(label),
            )
        )
    return tuple(cases)


def load_bird_jsonl(
    path: str | Path,
    *,
    preserve_evaluator_details: bool = False,
) -> list[BirdInteractRecord]:
    source = Path(path)
    records: list[BirdInteractRecord] = []
    with source.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}: {exc.msg}") from exc
            if not isinstance(raw, Mapping):
                raise ValueError(f"line {line_number} must contain a JSON object")
            try:
                record = parse_bird_interact_record(
                    raw,
                    preserve_evaluator_details=preserve_evaluator_details,
                )
            except ValueError as exc:
                raise ValueError(f"invalid BIRD record on line {line_number}: {exc}") from exc
            records.append(record)
    return records


def summarize_bird_records(records: Sequence[BirdInteractRecord]) -> BirdDatasetStats:
    type_counts: Counter[str] = Counter()
    masked = 0
    critical_count = 0
    noncritical_count = 0
    knowledge_count = 0
    multiple_critical = 0
    with_query = 0
    with_gold = 0
    with_tests = 0

    for record in records:
        critical_count += len(record.critical_ambiguities)
        noncritical_count += len(record.noncritical_ambiguities)
        knowledge_count += len(record.knowledge_ambiguities)
        multiple_critical += int(len(record.critical_ambiguities) > 1)
        with_query += int(record.evaluator_query is not None)
        with_gold += int(record.has_gold_sql)
        with_tests += int(record.has_test_cases)
        for label in (
            *record.critical_ambiguities,
            *record.noncritical_ambiguities,
            *record.knowledge_ambiguities,
        ):
            type_counts[label.ambiguity_type] += 1
            masked += int(label.masked)

    return BirdDatasetStats(
        records=len(records),
        critical_ambiguities=critical_count,
        noncritical_ambiguities=noncritical_count,
        knowledge_ambiguities=knowledge_count,
        records_with_multiple_critical=multiple_critical,
        masked_ambiguities=masked,
        ambiguity_type_counts=dict(type_counts),
        records_with_query=with_query,
        records_with_gold_sql=with_gold,
        records_with_test_cases=with_tests,
    )
