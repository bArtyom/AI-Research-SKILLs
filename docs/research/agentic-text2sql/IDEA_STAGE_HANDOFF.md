# Idea-Stage Handoff: Agentic Text-to-SQL Research Program

**Status:** idea/research-design stage complete  
**Date:** 2026-08-23  
**Branch:** `research-agentic-text2sql-2026`  
**Important:** This document marks the stopping point before real scientific experimentation. The remaining work is intended to be run on a research machine with benchmark data, model access, and reproducible experiment infrastructure.

## 1. Executive decision

After surveying contemporary Text-to-SQL, SQL-agent, interactive benchmark, debugging, verification, test-time scaling, and cross-domain literature, the strongest research portfolio is not a single pipeline but a staged program with three priorities:

1. **DiagSQL — Semantic Diagnosis Before SQL Repair**: highest near-term paper potential.
2. **SparseWorldSQL — Sparse Semantic Support Recovery for Giant Schemas**: strongest method-centric follow-up.
3. **ProvArgSQL — Provenance + Argumentation for Conflicting Enterprise Semantics**: highest-risk, most problem-redefining direction.

AIDA-SQL remains useful as the broader agentic substrate, but it should not be the first paper unless adaptive information acquisition itself becomes the strongest empirical finding.

The main research lesson is:

> The next important Text-to-SQL problem is increasingly not SQL decoding. It is deciding what the user means, what evidence is missing, which assumptions are wrong, which semantic world is currently valid, and what minimum interaction is needed before producing an auditable executable answer.

---

## 2. Recommended primary project: DiagSQL

### 2.1 Core thesis

A failing Text-to-SQL/Data-Agent trajectory should not immediately trigger whole-query regeneration. The system should first materialize and diagnose the **latent semantic assumptions** that produced the query.

Assumption families include:

- metric definition
- entity definition
- temporal interpretation
- aggregation grain
- join/path/cardinality
- filters and inclusion/exclusion rules
- value mapping
- business rules
- NULL semantics
- deduplication conventions

Then use the loop:

```text
request
  -> semantic assumptions
  -> semantic plan
  -> SQL / execution
  -> conflict evidence
  -> ranked diagnoses
  -> discriminating measurement
  -> refined diagnosis
  -> constrained semantic repair
```

### 2.2 Intended novelty boundary

Do **not** claim:

- first SQL fault localization;
- first SQL repair;
- first use of model-based diagnosis in databases;
- first SQL counterexample generation;
- first execution-guided SQL correction.

The intended contribution is narrower and more defensible:

> Diagnose latent semantic assumptions between natural-language intent and SQL, actively acquire measurements that discriminate among competing semantic diagnoses, and constrain repair to the diagnosed semantic subgraph.

### 2.3 Why this is the strongest first paper

- Existing SQL debugging remains difficult, so there is empirical headroom.
- BIRD-INTERACT/Mini-Interact exposes ambiguity and interaction, which naturally supplies measurement actions.
- Classical model-based diagnosis gives a mature algorithmic backbone: conflict sets, minimal diagnoses, sequential measurement.
- Delta debugging gives a principled way to isolate compact failure-inducing semantic sets.
- The hypothesis is falsifiable and easy to ablate: does explicit diagnosis help repair under matched evidence and cost?

### 2.4 Minimum publishable experiment

Recommended first benchmark stack:

- Mini-Interact first for ambiguity-heavy SQLite/SELECT-only experiments;
- BIRD-INTERACT after mechanics are stable;
- BIRD-CRITIC only on a carefully filtered semantic-compatible subset;
- optionally Spider 2.0 / LiveSQLBench later for transfer.

Core systems to compare under matched budgets:

```text
Direct Regeneration
Fixed Evidence + Regeneration
LLM Root-Cause Classifier + Repair
DiagSQL Static Diagnosis
DiagSQL Active Diagnosis
Oracle Diagnosis + Repair
```

Primary metrics:

- task repair success
- semantic root-cause Top-1 / Top-k
- measurement count
- user clarification turns
- DB/tool calls
- token cost / latency
- repair-scope fraction
- success-cost Pareto frontier

The key result to look for is not a small accuracy gain in isolation. The strongest result would be:

> At matched success, DiagSQL uses fewer expensive observations; or at matched cost, DiagSQL produces substantially higher semantic repair success.

### 2.5 High-value ablations

- no diagnosis, same evidence
- diagnosis without active measurement
- active measurement without diagnosis-constrained repair
- hard conflicts only vs hard + soft conflicts
- clause-level fault candidates vs semantic-assumption candidates
- random measurement vs entropy reduction vs cost-aware utility
- oracle assumption graph vs LLM-extracted assumption graph
- oracle conflict mapping vs learned/LLM conflict extraction
- whole-query regeneration vs diagnosis-constrained regeneration

### 2.6 Failure conditions that should kill or redirect the idea

DiagSQL should be deprioritized if one or more of the following occurs consistently:

- assumption extraction is too unreliable for diagnosis to add signal;
- direct repair with the same evidence performs equally well at the same cost;
- active measurement chooses no better actions than a fixed heuristic pipeline;
- most benchmark failures are SQL/runtime errors rather than latent semantic errors;
- diagnosis accuracy does not correlate with repair success;
- constrained repair prevents recovery more often than it helps.

If diagnosis itself works but assumption extraction fails, the correct next paper may be **semantic assumption extraction/localization**, not full DiagSQL.

---

## 3. Second project: SparseWorldSQL

### 3.1 Core thesis

Large-schema Text-to-SQL should be modeled as **sparse semantic support recovery**, not only top-k schema retrieval.

Enterprise databases may expose thousands to tens of thousands of columns, while a single analytical question usually depends on a small semantic support set.

Instead of independently ranking schema elements, jointly infer:

```text
metric
entity
fact table
dimension tables
join path
time field
filters
grain
```

under structural consistency constraints.

### 3.2 Borrowed machinery

- sparse coding / compressed sensing
- structured sparsity
- factor graphs / belief propagation
- submodular observation selection
- multiscale schema abstraction

### 3.3 Strongest empirical claim

The paper becomes compelling if it can show a scaling result such as:

> Recover comparable or better semantic accuracy while observing only a small fraction of the available schema.

Plot:

```text
accuracy / task success
vs
schema tokens observed / columns inspected / DB metadata calls
```

Possible new metrics:

- Semantic Support Recall@K
- Join-Support Recall@K
- Columns Inspected per Solved Task
- Schema Tokens per Successful Query
- Semantic Bits per Solved Query

### 3.4 Main risk

If the final implementation collapses into ordinary neural retrieval with a sparse loss, novelty will be weak. The research value comes from **joint structured support recovery and adaptive observation**, not merely L1 regularization.

---

## 4. Third project: ProvArgSQL

### 4.1 Core thesis

Enterprise semantics may not admit one globally correct ontology. Different teams may maintain locally valid but mutually incompatible definitions.

Represent each answer as an evidence-supported argument rather than a bare SQL string.

### 4.2 Borrowed machinery

- database provenance / provenance semirings
- abstract argumentation
- defeasible and non-monotonic reasoning
- temporal provenance
- semantic versioning / business-rule drift

### 4.3 Example

Finance may support:

```text
Revenue = invoiced amount - refunds
```

while Growth supports:

```text
Revenue = completed-order amount
```

Both can be internally consistent and provenance-supported.

The system builds an argument graph rather than forcing a premature single truth:

```text
Finance definition -> SQL_A -> Answer_A
        attacks
Growth definition  -> SQL_B -> Answer_B
```

If only one admissible semantic extension survives, answer. If multiple survive, retrieve more evidence or ask the user.

### 4.4 Potential new correctness notion

**Epistemic SQL Correctness**:

> An answer is acceptable only if it is supported by an admissible evidence/provenance extension under the current semantic context.

### 4.5 Main risk

Evaluation is much harder than standard execution accuracy. This direction likely requires a purpose-built benchmark or carefully constructed business-rule-drift subset.

---

## 5. Strong reserve directions

These should remain in the idea bank but should not displace the three primary programs without new evidence.

### AIDA-SQL

Treat Text-to-SQL as cost-sensitive active information acquisition under partial observability. Strong as infrastructure and as a broader framing.

### RG-SLAM SQL

Multiscale schema abstraction plus SLAM-style incremental mapping of an unknown organizational data world. Interesting for extreme schemas and long-lived agents.

### ECC-SQL

Generate redundant semantic representations — NL canonical form, semantic IR, SQL, grain, join graph, invariants — and use disagreement as semantic parity-check failure.

### Scientific SQL Agent

Require hypotheses, falsifiers, experiments, SQL, observations, belief updates, and replication. Strong long-horizon benchmark idea, but too broad for the first implementation.

### SheafSQL

Model local organizational semantics that may fail to glue into one globally consistent ontology. Mathematically attractive, but benchmark construction is the main bottleneck.

### ImmuneSQL

Maintain evolving specialist error detectors with memory and adaptation instead of a static verifier bank. Better as a lifelong-agent follow-up.

---

## 6. Ideas intentionally deprioritized

The following are useful ingredients but are currently too crowded or too incremental to be the main paper contribution by themselves:

- generic multi-agent role decomposition
- more SQL self-consistency sampling
- ordinary RAG over schema/docs
- generic LLM critic + rewrite
- fixed generate-execute-repair loops
- beam search over SQL strings
- counterexample generation without a stronger surrounding formulation
- test-time scaling without a novel allocation policy
- generic tool-routing prompts

These can be baselines or components, but should not be positioned as the central research novelty.

---

## 7. Research artifacts already prepared

### Landscape and idea maps

- `docs/research/agentic-text2sql/README.md`
- `docs/research/agentic-text2sql/IDEAS.md`
- `docs/research/agentic-text2sql/MOONSHOTS.md`
- `docs/research/agentic-text2sql/CROSS_DOMAIN_IDEAS.md`
- `docs/research/agentic-text2sql/EXOTIC_IDEA_ATLAS.md`
- `docs/research/agentic-text2sql/REFERENCES.md`

### AIDA-SQL

- `docs/research/agentic-text2sql/ARCHITECTURE.md`
- `docs/research/agentic-text2sql/EXPERIMENTS.md`
- `demos/agentic-text2sql-lab/`

### DiagSQL

- `docs/superpowers/specs/2026-08-23-diagsql-design.md`
- `docs/superpowers/plans/2026-08-23-diagsql-mvp.md`
- `docs/superpowers/specs/2026-08-23-diagsql-bird-interact-adapter-design.md`
- `docs/superpowers/plans/2026-08-23-diagsql-bird-interact-adapter.md`
- `demos/diagsql-lab/`

The demo code is scaffolding for mechanics and interface validation. Its toy benchmark numbers are not scientific evidence.

---

## 8. Recommended experiment order for handoff

When moving to a machine with model and dataset access, the lowest-risk sequence is:

1. **Dataset audit** — quantify Mini-Interact ambiguity families and leakage-safe fields.
2. **Oracle-assumption experiment** — bypass LLM extraction and test whether diagnosis mechanics help at all.
3. **Oracle-conflict experiment** — isolate active-measurement value from conflict-extraction noise.
4. **Matched-budget repair comparison** — direct repair vs diagnosis-conditioned repair.
5. **Structured LLM assumption extraction** — only after the symbolic core proves useful.
6. **Real active measurements** — user simulator, knowledge retrieval, schema inspection, diagnostic SQL.
7. **Multi-fault episodes** — only after single-fault behavior is stable.
8. **Transfer** — BIRD-INTERACT full setting, BIRD-CRITIC semantic subset, then larger enterprise benchmarks.

This ordering is designed so negative results remain informative. For example, if oracle diagnosis does not improve repair, there is no reason to spend time training assumption extractors.

---

## 9. Suggested paper framing if DiagSQL works

Working title:

**Diagnose Before You Repair: Active Semantic Fault Localization for Interactive Text-to-SQL Agents**

One-sentence pitch:

> We show that many executable Text-to-SQL failures originate in latent semantic assumptions rather than SQL syntax, and that explicit model-based diagnosis plus cost-aware discriminating measurements can localize these faults and improve repair under matched interaction budgets.

Core contribution structure:

1. problem formulation: latent semantic-assumption diagnosis;
2. assumption/conflict/diagnosis representation;
3. active measurement policy;
4. diagnosis-constrained repair;
5. leak-safe interactive benchmark construction;
6. matched-budget evaluation and root-cause analysis.

---

## 10. Stop line

The idea stage is considered complete at this point.

No further benchmark runs, model experiments, hyperparameter tuning, leaderboard comparisons, or claims of scientific improvement should be made from this branch without a dedicated experiment environment and reproducibility setup.

The next action belongs to the experimental phase.