# DiagSQL MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dependency-free, executable DiagSQL research scaffold that diagnoses latent semantic assumptions from conflicts, chooses cost-aware discriminating measurements, minimizes semantic failure sets, and constrains repair to the diagnosed assumption subgraph.

**Architecture:** Implement DiagSQL as a small Python package under `demos/diagsql-lab/`. The core diagnosis engine is deterministic and LLM-independent; measurement selection is information-theoretic; a controlled simulator supplies hidden semantic faults and measurement outcomes; a CLI benchmark demonstrates diagnosis and cost behavior without API keys.

**Tech Stack:** Python 3.11+ standard library only (`dataclasses`, `enum`, `math`, `itertools`, `typing`, `unittest`, `random`, `json`).

**Spec:** `docs/superpowers/specs/2026-08-23-diagsql-design.md`

## Global Constraints

- First implementation is **Variant A: logic-first, training-free DiagSQL**.
- Use only Python standard-library dependencies in the MVP.
- Keep the diagnosis engine independent of any LLM API.
- Focus on read-only analytical semantic faults; do not implement DML/DDL repair.
- Separate diagnosis quality from assumption-extraction quality by using controlled explicit assumption graphs.
- Hard conflicts determine valid diagnoses; soft conflicts rank otherwise-valid diagnoses.
- Semantic delta debugging claims only 1-minimality under its tested reduction operator.
- Repair is constrained to the diagnosed assumptions and their dependency descendants by default.
- Every public component must have deterministic unit tests.

---

## File map

```text
demos/diagsql-lab/
├── README.md                       # how to run, research claims, limitations
├── benchmark.py                    # executable controlled comparison
├── diagsql/
│   ├── __init__.py                 # stable public exports
│   ├── model.py                    # assumption graph, conflicts, diagnoses
│   ├── diagnosis.py                # minimal hitting sets + ranking
│   ├── measurement.py              # information gain + cost-aware selection
│   ├── delta.py                    # semantic ddmin
│   ├── repair.py                   # diagnosis-constrained repair scope
│   └── simulator.py                # controlled hidden-fault episodes
└── tests/
    ├── test_model.py
    ├── test_diagnosis.py
    ├── test_measurement.py
    ├── test_delta.py
    ├── test_repair.py
    └── test_simulator.py
```

Each module has one responsibility. `model.py` contains no algorithms beyond graph traversal. `diagnosis.py` does not know about simulations or SQL. `measurement.py` only reasons over diagnosis distributions and measurement outcome models. `simulator.py` is the only module that knows hidden ground truth.

---

### Task 1: Core semantic-assumption data model

**Files:**
- Create: `demos/diagsql-lab/diagsql/model.py`
- Create: `demos/diagsql-lab/diagsql/__init__.py`
- Create: `demos/diagsql-lab/tests/test_model.py`

**Interfaces:**
- Produces: `Assumption`, `Conflict`, `Diagnosis`, `AssumptionGraph`, `diagnosis_key`
- Later tasks consume these types directly.

- [ ] **Step 1: Write the failing graph tests**

```python
# demos/diagsql-lab/tests/test_model.py
import unittest

from diagsql.model import Assumption, AssumptionGraph, Conflict, Diagnosis, diagnosis_key


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.graph = AssumptionGraph([
            Assumption("metric", "metric", "revenue means net revenue", confidence=0.8),
            Assumption("amount", "schema", "orders.amount is the revenue source", dependencies=("metric",)),
            Assumption("refund", "filter", "refunds must be excluded", dependencies=("amount",)),
            Assumption("region", "schema", "customers.region is the grouping dimension"),
        ])

    def test_descendants_follow_dependency_edges(self):
        self.assertEqual(self.graph.descendants({"metric"}), {"amount", "refund"})

    def test_rejects_unknown_dependencies(self):
        with self.assertRaisesRegex(ValueError, "unknown dependency"):
            AssumptionGraph([Assumption("x", "metric", "x", dependencies=("missing",))])

    def test_conflict_must_not_be_empty(self):
        with self.assertRaisesRegex(ValueError, "at least one assumption"):
            Conflict(frozenset(), evidence_id="e")

    def test_diagnosis_key_is_stable(self):
        diagnosis = Diagnosis(frozenset({"refund", "metric"}), score=2.0)
        self.assertEqual(diagnosis_key(diagnosis), ("metric", "refund"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the model tests and verify they fail**

Run:

```bash
cd demos/diagsql-lab
python -m unittest -v tests.test_model
```

Expected: import failure because `diagsql.model` does not exist.

- [ ] **Step 3: Implement the minimal model**

```python
# demos/diagsql-lab/diagsql/model.py
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
```

```python
# demos/diagsql-lab/diagsql/__init__.py
from .model import Assumption, AssumptionGraph, Conflict, Diagnosis, diagnosis_key

__all__ = ["Assumption", "AssumptionGraph", "Conflict", "Diagnosis", "diagnosis_key"]
```

- [ ] **Step 4: Run the model tests and verify they pass**

Run:

```bash
cd demos/diagsql-lab
python -m unittest -v tests.test_model
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add demos/diagsql-lab/diagsql demos/diagsql-lab/tests/test_model.py
git commit -m "feat(diagsql): add semantic assumption model"
```

---

### Task 2: Minimal hitting-set diagnosis and weighted ranking

**Files:**
- Create: `demos/diagsql-lab/diagsql/diagnosis.py`
- Create: `demos/diagsql-lab/tests/test_diagnosis.py`
- Modify: `demos/diagsql-lab/diagsql/__init__.py`

**Interfaces:**
- Consumes: `Conflict`, `Diagnosis`, `AssumptionGraph`
- Produces:
  - `minimal_hitting_sets(conflicts, max_cardinality=3, limit=20) -> list[frozenset[str]]`
  - `rank_diagnoses(graph, conflicts, fault_priors=None, max_cardinality=3, limit=20, cardinality_penalty=0.1, soft_penalty=1.0) -> list[Diagnosis]`

- [ ] **Step 1: Write failing diagnosis tests**

```python
# demos/diagsql-lab/tests/test_diagnosis.py
import unittest

from diagsql.diagnosis import minimal_hitting_sets, rank_diagnoses
from diagsql.model import Assumption, AssumptionGraph, Conflict


class DiagnosisTests(unittest.TestCase):
    def test_minimal_hitting_sets_for_two_conflicts(self):
        conflicts = [
            Conflict(frozenset({"metric", "filter"}), "e1"),
            Conflict(frozenset({"filter", "time"}), "e2"),
        ]
        result = set(minimal_hitting_sets(conflicts, max_cardinality=2))
        self.assertEqual(result, {frozenset({"filter"}), frozenset({"metric", "time"})})

    def test_non_minimal_supersets_are_removed(self):
        conflicts = [Conflict(frozenset({"metric"}), "e1")]
        self.assertEqual(minimal_hitting_sets(conflicts, max_cardinality=3), [frozenset({"metric"})])

    def test_soft_conflict_ranks_consistent_diagnosis_first(self):
        graph = AssumptionGraph([
            Assumption("metric", "metric", "metric"),
            Assumption("filter", "filter", "filter"),
            Assumption("time", "time", "time"),
        ])
        conflicts = [
            Conflict(frozenset({"metric", "filter"}), "hard", hard=True),
            Conflict(frozenset({"metric"}), "soft", hard=False, weight=2.0),
        ]
        ranked = rank_diagnoses(
            graph,
            conflicts,
            fault_priors={"metric": 0.2, "filter": 0.2, "time": 0.2},
            max_cardinality=1,
        )
        self.assertEqual(ranked[0].faulty_ids, frozenset({"metric"}))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run and verify failure**

```bash
cd demos/diagsql-lab
python -m unittest -v tests.test_diagnosis
```

Expected: import failure for `diagsql.diagnosis`.

- [ ] **Step 3: Implement diagnosis enumeration and ranking**

```python
# demos/diagsql-lab/diagsql/diagnosis.py
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
```

Update `__init__.py` to export `minimal_hitting_sets` and `rank_diagnoses`.

- [ ] **Step 4: Run diagnosis and model tests**

```bash
cd demos/diagsql-lab
python -m unittest -v tests.test_model tests.test_diagnosis
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add demos/diagsql-lab/diagsql/diagnosis.py demos/diagsql-lab/diagsql/__init__.py demos/diagsql-lab/tests/test_diagnosis.py
git commit -m "feat(diagsql): add conflict-based diagnosis engine"
```

---

### Task 3: Cost-aware active measurement planner

**Files:**
- Create: `demos/diagsql-lab/diagsql/measurement.py`
- Create: `demos/diagsql-lab/tests/test_measurement.py`
- Modify: `demos/diagsql-lab/diagsql/__init__.py`

**Interfaces:**
- Consumes: `Diagnosis`, `diagnosis_key`
- Produces:
  - `Measurement(id, cost, outcome_likelihoods)`
  - `normalize_diagnosis_probabilities(diagnoses) -> list[float]`
  - `expected_information_gain(measurement, diagnoses, probabilities) -> float`
  - `choose_measurement(measurements, diagnoses, probabilities=None, lambda_cost=0.25) -> MeasurementChoice`

`Measurement.outcome_likelihoods` uses the shape:

```python
{
    "outcome_name": {
        ("fault_a",): 0.9,
        ("fault_b",): 0.1,
    }
}
```

All likelihoods for one diagnosis across outcomes must sum to 1.0 within tolerance.

- [ ] **Step 1: Write failing measurement tests**

```python
# demos/diagsql-lab/tests/test_measurement.py
import unittest

from diagsql.measurement import Measurement, choose_measurement, expected_information_gain
from diagsql.model import Diagnosis


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self.diagnoses = [
            Diagnosis(frozenset({"metric"}), 0.0),
            Diagnosis(frozenset({"join"}), 0.0),
        ]
        self.probs = [0.5, 0.5]

    def test_perfect_split_has_one_bit_information_gain(self):
        measurement = Measurement(
            "ask_metric",
            cost=1.0,
            outcome_likelihoods={
                "metric": {("metric",): 1.0, ("join",): 0.0},
                "join": {("metric",): 0.0, ("join",): 1.0},
            },
        )
        self.assertAlmostEqual(expected_information_gain(measurement, self.diagnoses, self.probs), 1.0)

    def test_cost_can_make_cheaper_test_preferred(self):
        expensive = Measurement(
            "ask_user",
            cost=4.0,
            outcome_likelihoods={
                "metric": {("metric",): 1.0, ("join",): 0.0},
                "join": {("metric",): 0.0, ("join",): 1.0},
            },
        )
        cheap = Measurement(
            "count_probe",
            cost=0.5,
            outcome_likelihoods={
                "high_dup": {("metric",): 0.2, ("join",): 0.8},
                "low_dup": {("metric",): 0.8, ("join",): 0.2},
            },
        )
        choice = choose_measurement([expensive, cheap], self.diagnoses, self.probs, lambda_cost=0.25)
        self.assertEqual(choice.measurement.id, "count_probe")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run and verify failure**

```bash
cd demos/diagsql-lab
python -m unittest -v tests.test_measurement
```

Expected: import failure.

- [ ] **Step 3: Implement entropy, validation, and action utility**

```python
# demos/diagsql-lab/diagsql/measurement.py
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
    for outcome, mapping in measurement.outcome_likelihoods.items():
        joint = [probabilities[i] * mapping.get(diagnosis_key(diagnosis), 0.0) for i, diagnosis in enumerate(diagnoses)]
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
    choices = []
    for measurement in measurements:
        gain = expected_information_gain(measurement, diagnoses, probs)
        utility = gain - lambda_cost * measurement.cost
        choices.append(MeasurementChoice(measurement, gain, utility))
    return max(choices, key=lambda item: (item.utility, -item.measurement.cost, item.measurement.id))
```

Export the new public types/functions from `__init__.py`.

- [ ] **Step 4: Run all tests through Task 3**

```bash
cd demos/diagsql-lab
python -m unittest -v tests.test_model tests.test_diagnosis tests.test_measurement
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add demos/diagsql-lab/diagsql/measurement.py demos/diagsql-lab/diagsql/__init__.py demos/diagsql-lab/tests/test_measurement.py
git commit -m "feat(diagsql): add active measurement planner"
```

---

### Task 4: Semantic delta debugging

**Files:**
- Create: `demos/diagsql-lab/diagsql/delta.py`
- Create: `demos/diagsql-lab/tests/test_delta.py`
- Modify: `demos/diagsql-lab/diagsql/__init__.py`

**Interfaces:**
- Produces: `ddmin(items: Sequence[str], fails: Callable[[tuple[str, ...]], bool]) -> tuple[str, ...]`
- Guarantee: returns a 1-minimal failure-inducing subset when the full input fails.

- [ ] **Step 1: Write failing ddmin tests**

```python
# demos/diagsql-lab/tests/test_delta.py
import unittest

from diagsql.delta import ddmin


class DeltaTests(unittest.TestCase):
    def test_finds_one_minimal_semantic_failure_set(self):
        def fails(items: tuple[str, ...]) -> bool:
            values = set(items)
            return {"fiscal_calendar", "comparison_window"}.issubset(values)

        result = ddmin(
            ["enterprise", "active", "fiscal_calendar", "comparison_window", "region"],
            fails,
        )
        self.assertEqual(set(result), {"fiscal_calendar", "comparison_window"})

    def test_requires_initial_failure(self):
        with self.assertRaisesRegex(ValueError, "full input does not fail"):
            ddmin(["a", "b"], lambda _: False)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run and verify failure**

```bash
cd demos/diagsql-lab
python -m unittest -v tests.test_delta
```

Expected: import failure.

- [ ] **Step 3: Implement classic ddmin-style reduction**

```python
# demos/diagsql-lab/diagsql/delta.py
from __future__ import annotations

from typing import Callable, Sequence


def ddmin(items: Sequence[str], fails: Callable[[tuple[str, ...]], bool]) -> tuple[str, ...]:
    current = tuple(items)
    if not fails(current):
        raise ValueError("full input does not fail")
    n = 2
    while len(current) >= 2:
        chunk_size = (len(current) + n - 1) // n
        chunks = [current[i:i + chunk_size] for i in range(0, len(current), chunk_size)]
        reduced = False
        for chunk in chunks:
            complement = tuple(item for item in current if item not in set(chunk))
            if complement and fails(complement):
                current = complement
                n = max(n - 1, 2)
                reduced = True
                break
        if reduced:
            continue
        if n >= len(current):
            break
        n = min(len(current), n * 2)
    return current
```

Export `ddmin` from `__init__.py`.

- [ ] **Step 4: Run all tests through Task 4**

```bash
cd demos/diagsql-lab
python -m unittest -v
```

Expected: all current tests PASS.

- [ ] **Step 5: Commit**

```bash
git add demos/diagsql-lab/diagsql/delta.py demos/diagsql-lab/diagsql/__init__.py demos/diagsql-lab/tests/test_delta.py
git commit -m "feat(diagsql): add semantic delta debugger"
```

---

### Task 5: Diagnosis-constrained repair scope

**Files:**
- Create: `demos/diagsql-lab/diagsql/repair.py`
- Create: `demos/diagsql-lab/tests/test_repair.py`
- Modify: `demos/diagsql-lab/diagsql/__init__.py`

**Interfaces:**
- Consumes: `AssumptionGraph`, `Diagnosis`
- Produces:
  - `RepairPlan(diagnosis, editable_ids, mode)`
  - `build_repair_plan(graph, diagnosis, global_threshold=0.6) -> RepairPlan`

Mode rules:

- `patch`: diagnosed closure is <= 30% of graph
- `local_regenerate`: diagnosed closure is > 30% and <= `global_threshold`
- `global_regenerate`: diagnosed closure exceeds `global_threshold`

- [ ] **Step 1: Write failing repair-scope tests**

```python
# demos/diagsql-lab/tests/test_repair.py
import unittest

from diagsql.model import Assumption, AssumptionGraph, Diagnosis
from diagsql.repair import build_repair_plan


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.graph = AssumptionGraph([
            Assumption("metric", "metric", "metric"),
            Assumption("amount", "schema", "amount", dependencies=("metric",)),
            Assumption("refund", "filter", "refund", dependencies=("amount",)),
            Assumption("region", "schema", "region"),
            Assumption("time", "time", "time"),
            Assumption("status", "filter", "status"),
            Assumption("entity", "entity", "entity"),
            Assumption("join", "join", "join"),
        ])

    def test_repair_scope_includes_dependency_descendants_only(self):
        plan = build_repair_plan(self.graph, Diagnosis(frozenset({"metric"}), 0.0))
        self.assertEqual(plan.editable_ids, frozenset({"metric", "amount", "refund"}))
        self.assertNotIn("region", plan.editable_ids)

    def test_small_leaf_fault_uses_patch_mode(self):
        plan = build_repair_plan(self.graph, Diagnosis(frozenset({"region"}), 0.0))
        self.assertEqual(plan.mode, "patch")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run and verify failure**

```bash
cd demos/diagsql-lab
python -m unittest -v tests.test_repair
```

Expected: import failure.

- [ ] **Step 3: Implement repair scope**

```python
# demos/diagsql-lab/diagsql/repair.py
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
```

Export the repair symbols from `__init__.py`.

- [ ] **Step 4: Run all tests**

```bash
cd demos/diagsql-lab
python -m unittest -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add demos/diagsql-lab/diagsql/repair.py demos/diagsql-lab/diagsql/__init__.py demos/diagsql-lab/tests/test_repair.py
git commit -m "feat(diagsql): constrain repair to diagnosed subgraph"
```

---

### Task 6: Controlled active-diagnosis simulator

**Files:**
- Create: `demos/diagsql-lab/diagsql/simulator.py`
- Create: `demos/diagsql-lab/tests/test_simulator.py`
- Modify: `demos/diagsql-lab/diagsql/__init__.py`

**Interfaces:**
- Consumes: graph, conflicts, diagnoses, measurement planner
- Produces:
  - `ControlledMeasurement(measurement, actual_outcome_by_fault, conflicts_by_outcome)`
  - `ControlledEpisode(graph, hidden_faults, initial_conflicts, measurements)`
  - `DiagnosticTrace`
  - `run_active_diagnosis(episode, max_steps=4, lambda_cost=0.25) -> DiagnosticTrace`

The controlled environment is allowed to know hidden ground truth; the diagnosis algorithm is not.

- [ ] **Step 1: Write failing simulator test**

```python
# demos/diagsql-lab/tests/test_simulator.py
import unittest

from diagsql.model import Assumption, AssumptionGraph, Conflict
from diagsql.measurement import Measurement
from diagsql.simulator import ControlledEpisode, ControlledMeasurement, run_active_diagnosis


class SimulatorTests(unittest.TestCase):
    def test_active_measurement_resolves_metric_vs_join(self):
        graph = AssumptionGraph([
            Assumption("metric", "metric", "wrong revenue definition"),
            Assumption("join", "join", "wrong join cardinality"),
        ])
        initial = [Conflict(frozenset({"metric", "join"}), "initial")]
        measurement = Measurement(
            "count_probe",
            cost=0.5,
            outcome_likelihoods={
                "duplication": {("metric",): 0.0, ("join",): 1.0},
                "no_duplication": {("metric",): 1.0, ("join",): 0.0},
            },
        )
        controlled = ControlledMeasurement(
            measurement=measurement,
            actual_outcome_by_fault={("metric",): "no_duplication", ("join",): "duplication"},
            conflicts_by_outcome={
                "duplication": (Conflict(frozenset({"join"}), "probe_join"),),
                "no_duplication": (Conflict(frozenset({"metric"}), "probe_metric"),),
            },
        )
        episode = ControlledEpisode(graph, frozenset({"join"}), tuple(initial), (controlled,))
        trace = run_active_diagnosis(episode, max_steps=2)
        self.assertEqual(trace.final_diagnoses[0].faulty_ids, frozenset({"join"}))
        self.assertEqual(trace.measurement_ids, ("count_probe",))
        self.assertAlmostEqual(trace.total_cost, 0.5)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run and verify failure**

```bash
cd demos/diagsql-lab
python -m unittest -v tests.test_simulator
```

Expected: import failure.

- [ ] **Step 3: Implement the controlled loop**

Implementation requirements:

```python
# key signatures for demos/diagsql-lab/diagsql/simulator.py
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
    final_diagnoses: tuple[Diagnosis, ...]
    measurement_ids: tuple[str, ...]
    outcomes: tuple[str, ...]
    total_cost: float
    conflict_count: int
```

`run_active_diagnosis` must:

1. rank diagnoses from current conflicts;
2. stop if top diagnosis is uniquely determined by a single remaining diagnosis;
3. select among unused measurements with `choose_measurement`;
4. reveal the environment outcome using `diagnosis_key(episode.hidden_faults)`;
5. append outcome-specific conflicts;
6. repeat until resolved, no measurements remain, or `max_steps` is reached.

When a measurement's likelihood table does not cover a newly generated diagnosis, exclude that measurement from the current candidate set rather than inventing a probability.

- [ ] **Step 4: Run all tests and verify deterministic pass**

```bash
cd demos/diagsql-lab
python -m unittest -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add demos/diagsql-lab/diagsql/simulator.py demos/diagsql-lab/diagsql/__init__.py demos/diagsql-lab/tests/test_simulator.py
git commit -m "feat(diagsql): add controlled active diagnosis episodes"
```

---

### Task 7: Executable benchmark and research-facing documentation

**Files:**
- Create: `demos/diagsql-lab/benchmark.py`
- Create: `demos/diagsql-lab/README.md`

**Interfaces:**
- CLI: `python benchmark.py`
- Output: JSON-like summary containing diagnosis accuracy, measurement cost, repair scope size, and a fixed-vs-active comparison over deterministic controlled episodes.

- [ ] **Step 1: Create a deterministic benchmark with at least three fault families**

`benchmark.py` must include controlled episodes for:

1. metric vs join ambiguity
2. time vs filter ambiguity
3. grain vs deduplication ambiguity

For each episode, report:

```python
{
    "hidden_faults": [...],
    "initial_top_diagnosis": [...],
    "final_top_diagnosis": [...],
    "diagnosis_correct": True,
    "measurements": [...],
    "measurement_cost": 0.0,
    "repair_mode": "patch",
    "repair_scope_size": 0,
}
```

Also compute aggregate:

```python
{
    "episodes": 3,
    "top1_diagnosis_accuracy": ...,
    "mean_measurement_cost": ...,
    "mean_repair_scope_fraction": ...,
}
```

- [ ] **Step 2: Run the benchmark**

```bash
cd demos/diagsql-lab
python benchmark.py
```

Expected: deterministic successful resolution for the three controlled episodes with finite non-zero diagnostic cost.

- [ ] **Step 3: Write `README.md` with exact research boundaries**

The README must state:

- this is a controlled research scaffold, not a benchmark result;
- ground-truth assumption graphs are explicit to isolate diagnosis quality;
- the MVP does not call an LLM and does not claim end-to-end Text-to-SQL performance;
- the next adapter target is BIRD-INTERACT ambiguity episodes, followed by compatible BIRD-CRITIC tasks;
- references to `docs/superpowers/specs/2026-08-23-diagsql-design.md` and the current implementation plan.

It must include commands:

```bash
cd demos/diagsql-lab
python -m unittest -v
python benchmark.py
```

- [ ] **Step 4: Run the full verification suite**

```bash
cd demos/diagsql-lab
python -m unittest -v
python benchmark.py
```

Expected: all unit tests PASS and benchmark completes without exceptions.

- [ ] **Step 5: Commit**

```bash
git add demos/diagsql-lab/benchmark.py demos/diagsql-lab/README.md
git commit -m "demo(diagsql): add controlled semantic diagnosis benchmark"
```

---

## Final verification checklist

After all tasks:

```bash
cd demos/diagsql-lab
python -m unittest -v
python benchmark.py
```

Confirm:

- every unit test passes;
- hard conflicts always constrain candidate diagnoses;
- soft conflicts change ranking but do not invalidate a hard-consistent diagnosis;
- the active planner can prefer a cheaper imperfect measurement over an expensive perfect one;
- delta debugging returns a 1-minimal tested failure set;
- repair scope contains diagnosed assumptions plus descendants and excludes unrelated assumptions;
- controlled hidden-fault episodes resolve deterministically;
- no external Python dependency or API key is required.

## Post-MVP research extensions — not part of this plan

After the controlled scaffold is validated, create separate plans for:

1. BIRD-INTERACT adapter using `amb_user_query`, ambiguity labels, HKB retrieval, and executable tests;
2. BIRD-CRITIC compatibility mapping and debugging adapter;
3. structured LLM assumption extraction and SQL-fragment alignment;
4. soft conflict calibration and learned diagnosis priors;
5. diagnosis-conditioned actual SQL patch generation;
6. matched-budget experimental harness across generators.
