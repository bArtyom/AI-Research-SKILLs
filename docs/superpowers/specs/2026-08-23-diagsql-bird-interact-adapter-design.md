# DiagSQL × BIRD-INTERACT Adapter Design

**Status:** approved continuation of the DiagSQL research program  
**Date:** 2026-08-23  
**Parent spec:** `docs/superpowers/specs/2026-08-23-diagsql-design.md`

## 1. Goal

Connect DiagSQL's explicit semantic-diagnosis machinery to the public structure of BIRD-INTERACT / Mini-Interact without leaking benchmark labels into the agent runtime.

The first adapter is deliberately **data-structural**, not yet an end-to-end BIRD submission agent. It should:

1. parse public BIRD-INTERACT JSON/JSONL records;
2. normalize critical, non-critical, and knowledge ambiguities;
3. create an agent-visible runtime task that excludes oracle annotations;
4. create a separate offline oracle view for controlled diagnosis experiments;
5. map ambiguity families to DiagSQL semantic fault types;
6. propose measurement/action families that match BIRD's interactive tool surface;
7. summarize ambiguity distributions in a downloaded dataset.

## 2. Why Mini-Interact first

The official BIRD-INTERACT project currently exposes a 300-task Mini-Interact variant built on SQLite and SELECT-only queries. It decouples priority ambiguity resolution from later follow-up tasks and focuses on knowledge-based ambiguity. This is a lower-friction research target than immediately standing up the full PostgreSQL/Docker environment.

The full BIRD-INTERACT benchmark has 600 tasks and supports both conversational and active agentic interaction over database/HKB/user-simulator environments. Its public task schema includes fields such as:

- `instance_id`
- `selected_database`
- `query` when available
- `amb_user_query`
- `user_query_ambiguity`
- `knowledge_ambiguity`
- `preprocess_sql`
- `clean_up_sqls`
- `sol_sql`
- `external_knowledge`
- `test_cases`
- `follow_up`

Ground-truth SQL and executable test cases may be withheld from the public crawled data to limit leakage. The adapter therefore must not require them.

## 3. Leakage boundary

This is the most important design constraint.

BIRD ambiguity annotations can contain fields such as:

```json
{
  "term": "performed better than usual",
  "sql_snippet": "WHERE ...",
  "is_mask": false,
  "type": "semantic_ambiguity"
}
```

`sql_snippet`, deleted-knowledge IDs, gold SQL, test cases, unambiguous reformulations, or evaluator-only ambiguity labels must never be passed to the runtime agent when measuring interactive performance.

The adapter therefore defines two views.

### 3.1 Runtime view

Visible to the agent:

```text
instance_id
selected_database
ambiguous user query
category/high-level metadata when benchmark rules permit
```

Future environment adapters may additionally expose information only through benchmark-legal actions such as schema inspection, column-meaning retrieval, knowledge retrieval, SQL execution, or asking the user simulator.

### 3.2 Oracle/evaluation view

Visible only to offline benchmark construction and scoring:

```text
critical ambiguity term
ambiguity type
masked flag
knowledge-ambiguity relation
sql snippet when locally available
unambiguous query when locally available
gold SQL/test cases when locally available
```

Code should make accidental crossing of this boundary difficult by using separate immutable dataclasses.

## 4. Normalized ambiguity model

Represent an annotation as:

```python
BirdAmbiguityLabel(
    label_id="critical:0",
    term="custom interaction score",
    ambiguity_type="knowledge_linking_ambiguity",
    masked=True,
    critical=True,
    source="user_query",
    sql_snippet=None,       # omitted unless explicit offline label mode
    deleted_knowledge=None,
)
```

Knowledge-level annotations use `source="knowledge"`.

Stable label IDs should be based on source and list index, not wording hashes, so repeated terms remain distinguishable.

## 5. Mapping BIRD ambiguity to DiagSQL fault families

Initial deterministic mapping:

| BIRD annotation | DiagSQL fault family | Typical active measurement |
|---|---|---|
| `knowledge_linking_ambiguity` | `business_rule` | retrieve knowledge / ask user |
| `knowledge_ambiguity` | `business_rule` | retrieve knowledge |
| `schema_linking_ambiguity` | `schema` | inspect schema / retrieve column meaning |
| `semantic_ambiguity` | `semantic` | ask user / cheap diagnostic probe |
| `intent_ambiguity` | `intent` | ask user |
| unknown | `other` | inspect evidence / ask user |

This mapping is a baseline, not a claim that annotation types equal causal fault types. Later experiments can learn or refine the mapping.

## 6. Offline single-fault diagnostic cases

A BIRD record can contain multiple critical ambiguities. For clean root-cause evaluation, generate one oracle diagnostic case per critical ambiguity:

```text
record news_5
  critical:0 -> case news_5::critical:0
  critical:1 -> case news_5::critical:1
```

Each case contains:

- runtime task
- one oracle hidden semantic fault
- normalized fault type
- legal measurement-family recommendations
- evaluator-only label metadata

This creates a controlled bridge between real benchmark ambiguity annotations and DiagSQL's diagnosis metrics without pretending that the public annotations alone reproduce the full interactive environment.

Multi-fault cases can be added later by grouping multiple critical ambiguities from the same record.

## 7. Measurement recommendations

The adapter should expose abstract recommendations rather than fake outcome probabilities.

```python
MeasurementRecommendation(
    action="retrieve_knowledge",
    target="custom interaction score",
    estimated_cost=1.0,
    rationale="knowledge-linking ambiguity"
)
```

The actual likelihood model `P(outcome | diagnosis, action)` belongs to a later BIRD environment/user-simulator integration. The structural adapter must not invent outcomes.

Suggested default costs are relative research placeholders:

- inspect schema: 0.5
- retrieve column meaning: 0.75
- retrieve knowledge: 1.0
- run diagnostic SQL: 1.0
- ask user: 2.0

They should be configurable once mapped to BIRD COIN or actual API/database costs.

## 8. Dataset statistics

Given downloaded JSONL, compute:

- record count
- critical ambiguity count
- non-critical ambiguity count
- knowledge ambiguity count
- counts by ambiguity type
- masked vs unmasked counts
- records with multiple critical ambiguities
- records with optional `query`
- records with optional test/gold fields populated

This is useful both for sanity checking and for deciding which DiagSQL failure families have enough support for statistically meaningful experiments.

## 9. File boundaries

Extend `demos/diagsql-lab/` with:

```text
diagsql/bird_interact.py       parser, leakage-safe views, mapping, stats
bird_adapter.py                JSONL inspection CLI
tests/test_bird_interact.py    deterministic synthetic fixtures
```

Do not vendor BIRD data into this repository.

## 10. Tests

Tests must prove:

1. critical/non-critical/knowledge ambiguity parsing;
2. missing optional fields are accepted;
3. runtime view does not contain `sql_snippet`, deleted knowledge, gold SQL, or test cases;
4. oracle mode preserves evaluator labels when explicitly requested;
5. ambiguity-to-fault mapping is deterministic;
6. recommended measurements correspond to fault family;
7. multiple critical ambiguities produce multiple single-fault cases;
8. JSONL statistics are correct on a synthetic fixture;
9. malformed records fail with useful errors.

## 11. Non-goals

This adapter does not yet:

- download BIRD datasets automatically;
- run BIRD's user simulator;
- execute SQLite/PostgreSQL databases;
- use hidden ground-truth SQL or test cases;
- generate SQL repairs;
- report BIRD success rate;
- claim that ambiguity annotations are complete causal explanations.

## 12. Follow-on experiment

After the structural adapter is green, the next experiment should use a locally downloaded Mini-Interact dataset and compute the real ambiguity distribution. Then implement one legal interactive environment adapter that exposes:

```text
ask_user
retrieve_knowledge
retrieve_column_meaning
inspect_schema
execute_sql
```

DiagSQL can then compare fixed action pipelines with diagnosis-conditioned action selection under matched BIRD COIN / turn budgets.

The first scientific result should be a **cost-vs-root-cause-resolution** curve, not end-to-end SQL accuracy alone.
