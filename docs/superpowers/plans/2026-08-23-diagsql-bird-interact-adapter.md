# DiagSQL BIRD-INTERACT Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a leak-safe parser and offline diagnostic-case adapter for BIRD-INTERACT / Mini-Interact public JSONL records.

**Architecture:** Keep benchmark parsing in a single dependency-free `bird_interact.py` module. Separate `BirdRuntimeTask` from evaluator-only `BirdInteractRecord`/`BirdAmbiguityLabel`, then derive single-fault oracle cases and abstract measurement recommendations without inventing user-simulator outcomes.

**Tech Stack:** Python 3.11+ standard library only.

**Spec:** `docs/superpowers/specs/2026-08-23-diagsql-bird-interact-adapter-design.md`

## Global Constraints

- Never expose `sql_snippet`, deleted-knowledge IDs, gold SQL, test cases, or unambiguous query through `BirdRuntimeTask`.
- Do not vendor BIRD data.
- Do not require withheld ground-truth/test-case fields.
- Do not fake `P(outcome | diagnosis, action)`; measurement recommendations are action templates only.
- Preserve the existing DiagSQL dependency-free test suite.

---

### Task 1: Parse BIRD records and ambiguity labels

**Files:**
- Create: `demos/diagsql-lab/diagsql/bird_interact.py`
- Create: `demos/diagsql-lab/tests/test_bird_interact.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class BirdAmbiguityLabel: ...
@dataclass(frozen=True)
class BirdInteractRecord: ...
@dataclass(frozen=True)
class BirdRuntimeTask: ...

def parse_bird_interact_record(raw: Mapping[str, Any], *, preserve_evaluator_details: bool = False) -> BirdInteractRecord: ...
def to_runtime_task(record: BirdInteractRecord) -> BirdRuntimeTask: ...
```

- [ ] Write tests with synthetic `user_query_ambiguity` containing `critical_ambiguity` and `non_critical_ambiguity`, plus `knowledge_ambiguity`.
- [ ] Run `python -m unittest -v tests.test_bird_interact` and confirm missing-module failure.
- [ ] Implement parsing, validation of `instance_id`/`selected_database`/`amb_user_query`, and optional-field handling.
- [ ] Assert runtime task contains only safe public task fields.
- [ ] Run the tests until green.

### Task 2: Oracle single-fault cases and fault mapping

**Files:**
- Modify: `demos/diagsql-lab/diagsql/bird_interact.py`
- Modify: `demos/diagsql-lab/tests/test_bird_interact.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class BirdDiagnosticCase: ...

def map_ambiguity_type(ambiguity_type: str) -> str: ...
def single_fault_cases(record: BirdInteractRecord) -> tuple[BirdDiagnosticCase, ...]: ...
```

- [ ] Add failing tests for mapping knowledge/schema/semantic/intent/unknown ambiguity types.
- [ ] Add failing test that two critical ambiguities produce two distinct `instance_id::critical:N` cases.
- [ ] Implement the minimal mapping and case generator.
- [ ] Verify tests pass.

### Task 3: Measurement recommendations

**Files:**
- Modify: `demos/diagsql-lab/diagsql/bird_interact.py`
- Modify: `demos/diagsql-lab/tests/test_bird_interact.py`

**Interface:**

```python
@dataclass(frozen=True)
class MeasurementRecommendation:
    action: str
    target: str
    estimated_cost: float
    rationale: str

def recommend_measurements(label: BirdAmbiguityLabel) -> tuple[MeasurementRecommendation, ...]: ...
```

Expected baseline mapping:

```text
business_rule -> retrieve_knowledge, ask_user
schema        -> inspect_schema, retrieve_column_meaning
semantic      -> ask_user, run_diagnostic_sql
intent        -> ask_user
other         -> ask_user
```

- [ ] Add failing tests for business-rule and schema recommendations.
- [ ] Implement deterministic recommendation templates and relative costs.
- [ ] Verify tests pass.

### Task 4: JSONL loading and dataset statistics

**Files:**
- Modify: `demos/diagsql-lab/diagsql/bird_interact.py`
- Create: `demos/diagsql-lab/bird_adapter.py`
- Modify: `demos/diagsql-lab/tests/test_bird_interact.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class BirdDatasetStats: ...
def load_bird_jsonl(path: str | Path, *, preserve_evaluator_details: bool = False) -> list[BirdInteractRecord]: ...
def summarize_bird_records(records: Sequence[BirdInteractRecord]) -> BirdDatasetStats: ...
```

- [ ] Write a failing temporary-file test for two JSONL rows and exact expected counts.
- [ ] Implement JSONL loader with line-numbered parse errors.
- [ ] Implement summary counts by ambiguity type and masked state.
- [ ] Add CLI `python bird_adapter.py /path/to/mini_interact.jsonl` that prints JSON statistics.
- [ ] Run adapter tests and full DiagSQL tests.

### Task 5: Public exports and documentation

**Files:**
- Modify: `demos/diagsql-lab/diagsql/__init__.py`
- Modify: `demos/diagsql-lab/README.md`

- [ ] Export stable adapter dataclasses/functions.
- [ ] Document Mini-Interact as the first recommended real dataset because it is SQLite/SELECT-only and currently 300 tasks.
- [ ] Document the leakage boundary and state explicitly that evaluator annotations are never runtime input.
- [ ] Run:

```bash
cd demos/diagsql-lab
python -m unittest -v
python benchmark.py
```

- [ ] Confirm the existing controlled benchmark remains unchanged and all tests pass.
