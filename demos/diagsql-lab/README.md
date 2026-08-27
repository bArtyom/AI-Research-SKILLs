# DiagSQL Lab

A dependency-free research scaffold for **semantic diagnosis before SQL repair**.

DiagSQL treats a failed Text-to-SQL/data-agent attempt as a diagnosis problem over explicit semantic assumptions such as metric definitions, entity meanings, time windows, aggregation grain, join semantics, filters, value mappings, and deduplication rules. Instead of immediately regenerating the whole query, the scaffold:

1. represents semantic assumptions and their dependency graph;
2. converts evidence into hard/soft conflict sets;
3. enumerates minimal hitting-set diagnoses;
4. ranks diagnoses with priors and soft evidence;
5. selects discriminating measurements by expected information gain minus cost;
6. optionally shrinks failure-inducing semantic sets with delta debugging;
7. restricts repair to diagnosed assumptions and their descendants.

This directory implements the logic-first MVP described in:

- [`../../docs/superpowers/specs/2026-08-23-diagsql-design.md`](../../docs/superpowers/specs/2026-08-23-diagsql-design.md)
- [`../../docs/superpowers/plans/2026-08-23-diagsql-mvp.md`](../../docs/superpowers/plans/2026-08-23-diagsql-mvp.md)

## Run

```bash
cd demos/diagsql-lab
python -m unittest -v
python benchmark.py
```

The MVP uses only the Python standard library and requires no API key.

## Components

```text
diagsql/model.py        explicit semantic assumptions, graph, conflicts, diagnoses
diagsql/diagnosis.py    minimal hitting sets + weighted diagnosis ranking
diagsql/measurement.py  entropy / expected information gain / cost-aware action choice
diagsql/delta.py        1-minimal semantic failure-set reduction
diagsql/repair.py       diagnosis-constrained repair scope
diagsql/simulator.py    controlled hidden-fault active-diagnosis episodes
diagsql/bird_interact.py leak-safe BIRD-INTERACT / Mini-Interact adapter
benchmark.py            deterministic research demonstration
bird_adapter.py         downloaded BIRD JSONL summary CLI
```

## Controlled benchmark

`benchmark.py` contains three deliberately small diagnostic episodes:

- metric vs join
- time vs filter
- grain vs deduplication

Each episode begins with a hard conflict that leaves two singleton diagnoses. A controlled measurement then provides discriminating evidence and creates a new conflict that isolates the hidden semantic fault.

A verified local run during implementation produced:

```text
29 unit tests: PASS
fixed top-1 diagnosis accuracy: 0.0
active top-1 diagnosis accuracy: 1.0
mean measurement cost: 0.4333
mean repair-scope fraction: 0.3889
```

These numbers are **not scientific benchmark results**. The episodes are constructed to demonstrate mechanics, and the hidden faults are intentionally chosen so the initial deterministic tie-break is wrong. The useful artifact is the executable diagnosis/measurement/repair contract, not the toy accuracy number.

## What this MVP proves and does not prove

It demonstrates that the following pieces can be made explicit and independently testable:

- semantic assumptions rather than only SQL clauses as fault candidates;
- multi-fault-compatible diagnosis through hitting sets;
- hard evidence vs soft ranking evidence;
- information-theoretic measurement selection with explicit cost;
- 1-minimal semantic delta debugging;
- dependency-aware constrained repair scope.

It does **not** yet demonstrate end-to-end Text-to-SQL improvement. In particular, it does not yet:

- infer assumption graphs from natural language with an LLM;
- derive conflicts from a real database, business docs, query plans, or user simulator;
- generate an actual SQL patch;
- evaluate BIRD, BIRD-INTERACT, BIRD-CRITIC, Spider 2.0, or LiveSQLBench.

Those separations are intentional: the first experiment should isolate whether diagnosis machinery is useful before adding model-dependent extraction and generation errors.

## Research lineage

The design is grounded in several established research lines rather than treating diagnosis as a metaphor:

- Reiter (1987), *A Theory of Diagnosis from First Principles* — conflict sets and diagnoses.
- de Kleer & Williams (1987), *Diagnosing Multiple Faults* — multiple faults and sequential diagnosis.
- Hou (1994), *A Theory of Measurement in Diagnosis from First Principles* — measurements that discriminate diagnoses.
- Feldman, Provan & van Gemund — active testing / sequential model-based diagnosis.
- Zeller & Hildebrandt (2002), *Simplifying and Isolating Failure-Inducing Input* — delta debugging.
- database-aware SQL fault localization and automatic SQL repair work predating LLMs.
- SWE-SQL/BIRD-CRITIC — realistic SQL debugging.
- BIRD-INTERACT — ambiguity, knowledge, user interaction, and active agentic database behavior.
- SpotIt/SpotIt+ and DPC — differentiating databases / minimal distinguishing databases for SQL verification.

The intended novelty boundary is therefore narrow: **diagnose latent semantic assumptions that mediate user intent and SQL, actively gather evidence to distinguish competing diagnoses, then constrain repair to the diagnosed semantic subgraph.**

## Next experiment

The structural BIRD-INTERACT adapter is now in place. The next scientific step is to run it against a locally downloaded Mini-Interact JSONL file, measure the real ambiguity distribution, and then connect benchmark-legal actions to an interactive environment:

```text
ambiguous task
   -> leak-safe runtime view
   -> candidate semantic assumptions
   -> ask_user / retrieve_knowledge / retrieve_column_meaning / inspect_schema / execute_sql
   -> conflicts and diagnosis update
   -> constrained repair
   -> executable evaluation
```

That experiment should compare fixed retrieval/regeneration against diagnosis-conditioned action selection under matched turn/BIRD-COIN budgets. Afterward, map BIRD-CRITIC tasks into semantic-compatible vs purely SQL/runtime categories instead of claiming DiagSQL applies uniformly to all debugging issues.

## BIRD-INTERACT / Mini-Interact adapter

`diagsql/bird_interact.py` adds a dependency-free structural adapter for downloaded BIRD-INTERACT JSONL files. The recommended first real dataset is Mini-Interact: the official project describes it as a 300-task SQLite, SELECT-only benchmark focused on knowledge-based ambiguity, making it much easier to iterate on diagnosis logic before moving to the full PostgreSQL environment.

The adapter deliberately separates two views:

```text
BirdRuntimeTask
    agent-visible: instance id, database, ambiguous query, safe task metadata

BirdInteractRecord / BirdAmbiguityLabel
    evaluator-side: normalized ambiguity annotations and optional oracle details
```

By default, evaluator details such as `sql_snippet`, deleted-knowledge IDs, the unambiguous query, gold SQL, and test cases are not preserved in ambiguity labels and never appear in `BirdRuntimeTask`. Use `preserve_evaluator_details=True` only for offline benchmark construction or analysis, never as runtime agent context.

Inspect a locally downloaded dataset with:

```bash
cd demos/diagsql-lab
python bird_adapter.py /path/to/mini_interact.jsonl
```

The CLI reports record counts, critical/non-critical/knowledge ambiguity counts, ambiguity-type frequencies, masked annotations, multi-critical tasks, and availability of optional evaluator fields. It does not download the benchmark or expose hidden ground truth to an agent.

For controlled root-cause evaluation, `single_fault_cases(record)` produces one evaluator-only diagnostic case per critical ambiguity and maps BIRD annotation families into coarse DiagSQL fault families (`business_rule`, `schema`, `semantic`, `intent`, `other`). `recommend_measurements()` then proposes legal action families such as knowledge retrieval, schema inspection, column-meaning retrieval, diagnostic SQL, or user clarification. These are only action templates: the adapter intentionally does not invent outcome probabilities for the real BIRD user/database environment.
