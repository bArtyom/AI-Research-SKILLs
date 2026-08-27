# DiagSQL: Semantic Diagnosis Before SQL Repair

**Status:** design specification  
**Date:** 2026-08-23  
**Branch:** `research-agentic-text2sql-2026`

## 1. Executive summary

DiagSQL reframes failure recovery for Text-to-SQL and data agents as **model-based diagnosis over latent semantic assumptions** rather than immediate SQL regeneration.

A Text-to-SQL system does not only make mistakes in SQL syntax or SQL clauses. It may adopt an incorrect metric definition, entity interpretation, time scope, aggregation grain, join assumption, value mapping, business rule, or deduplication convention before a SQL string is produced. These assumptions can yield SQL that parses, executes, and even passes local checks while still answering the wrong question.

DiagSQL therefore introduces a loop:

```text
user request
   |
   v
explicit semantic assumptions
   |
   v
semantic plan -> SQL -> execution
                  |
                  v
             observations
                  |
                  v
          conflict extraction
                  |
                  v
        candidate diagnoses
                  |
          active measurement
                  |
                  v
       diagnosis refinement
                  |
                  v
       constrained repair
```

The central research hypothesis is:

> A data agent that explicitly diagnoses which latent semantic assumptions are likely wrong, then chooses low-cost measurements that discriminate among competing diagnoses, can improve repair success and reduce unnecessary regeneration, tool calls, user interruptions, and database cost.

The initial paper should be **hybrid symbolic-neural** rather than end-to-end learned. LLMs propose assumptions, semantic plans, and evidence mappings; deterministic and probabilistic diagnostic machinery maintains conflicts and diagnoses; active measurement chooses the next action; repair is restricted to diagnosed semantic components and their dependents.

The near-term objective is not to build a universal data agent. It is to establish that **diagnosis is a useful intermediate computational object between failure observation and repair**.

---

## 2. Research question and novelty boundary

### 2.1 Primary research question

Can explicit diagnosis over latent semantic assumptions improve Text-to-SQL/Data-Agent repair compared with direct regeneration or generic self-correction?

### 2.2 Secondary questions

1. Can conflict sets derived from heterogeneous evidence localize semantic faults accurately enough to constrain repair?
2. Can active measurements reduce the number and cost of observations needed to identify the root cause?
3. Does semantic delta debugging find compact failure-inducing assumption sets that correlate with repairability?
4. Which evidence channels are most useful for different fault types?
5. Does better diagnosis improve repair even when the underlying SQL generator is unchanged?
6. How much of the gain comes from diagnosis itself versus simply collecting more evidence?

### 2.3 What we do **not** claim

DiagSQL must not claim to be the first SQL fault-localization or SQL-repair system. Database-aware fault localization existed well before LLM-based Text-to-SQL, including work that ranks suspicious statement-SQL and statement-attribute tuples. Automatic SQL repair has also targeted JOIN and WHERE faults.

DiagSQL also must not claim to be the first use of model-based diagnosis in databases. Database causality, repairs, and consistency-based diagnosis have established theoretical connections.

DiagSQL also must not claim that counterexample generation for SQL is novel. Recent systems such as SpotIt/SpotIt+ and DPC actively construct differentiating database instances or minimal distinguishing databases for SQL verification and candidate selection.

### 2.4 Intended novelty claim

The intended contribution is narrower:

> A framework for diagnosing **latent semantic assumptions that mediate natural-language intent and SQL**, using heterogeneous conflict evidence plus sequential, cost-aware measurements, before performing diagnosis-constrained repair.

The unit of diagnosis is not a token, AST node, or SQL clause. It is an assumption such as:

- `metric_definition = net_revenue`
- `entity_definition = account ARR >= 100k`
- `time_scope = fiscal_Q2`
- `grain = one_row_per_customer`
- `join_path = accounts -> subscriptions -> invoices`
- `deduplication = distinct customer_id`
- `cancelled_records = excluded`

This is the novelty boundary that should remain stable throughout implementation and evaluation.

---

## 3. Literature-grounded motivation

### 3.1 Model-based diagnosis

Reiter's 1987 theory defines diagnosis by comparing an expected system model with observations and identifying components whose abnormality explains the discrepancy. Minimal diagnoses can be obtained through conflict sets and minimal hitting sets.

De Kleer and Williams' GDE extends this perspective to multiple faults and sequential diagnosis, explicitly using new measurements to discriminate among competing diagnoses. Later work formalized measurement theory and developed scalable query/measurement selection strategies, including information-theoretic and cost-aware criteria.

Transfer to DiagSQL:

- physical component -> semantic assumption
- sensor observation -> schema/data/doc/execution observation
- fault hypothesis -> semantic diagnosis
- probe/measurement -> agent tool action
- component replacement -> constrained semantic repair

### 3.2 Delta debugging

Delta debugging automatically reduces a failure-inducing input/configuration to a small subset that still reproduces the failure. For DiagSQL, the object being minimized is a set of semantic assumptions or semantic-plan clauses rather than source-code characters.

The practical target is a **1-minimal semantic failure set**, not a claim of globally minimum causality under arbitrary non-monotonic behavior.

### 3.3 Fault localization and automated program repair

Software engineering work repeatedly shows that localization quality affects repair efficiency and correctness. Joint localization-and-repair and repair-specific fault localization outperform uninformed search in several settings.

This supports DiagSQL's main causal hypothesis: reducing the repair search space around plausible semantic faults should improve repair effectiveness or cost-efficiency.

### 3.4 Current Text-to-SQL repair/verification frontier

Execution-guided decoding established early that program execution can eliminate invalid SQL candidates. DIN-SQL added decomposition and self-correction. Recent systems go much further:

- SWE-SQL/BIRD-CRITIC creates realistic SQL debugging tasks and demonstrates that debugging remains difficult.
- DeepEye-SQL uses software-engineering-style deterministic verification and targeted revision.
- DPC uses a minimal distinguishing database plus a Python/Pandas solution for cross-paradigm candidate selection.
- SpotIt/SpotIt+ uses bounded equivalence verification and differentiating databases.
- BIRD-INTERACT introduces ambiguous user requests, external knowledge, dynamic interaction, and executable test cases.

These works strengthen the need for DiagSQL while also defining what it must avoid duplicating. DiagSQL should focus on **root-cause hypothesis management and measurement selection**, not merely verification.

---

## 4. Formal problem formulation

### 4.1 Episode

A diagnostic episode is

\[
E = (u, D, K, q_0, O_0, B)
\]

where:

- \(u\): natural-language task or user request
- \(D\): database environment
- \(K\): accessible external knowledge (schema descriptions, business docs, metadata, query history)
- \(q_0\): initial SQL or failing data-agent program
- \(O_0\): initial observations such as execution result, test failure, user feedback, or verifier disagreement
- \(B\): diagnostic budget over tokens, DB calls, latency, user interruptions, and risk

### 4.2 Assumptions

The agent materializes a finite set of assumptions

\[
H = \{h_1, \ldots, h_n\}.
\]

Each assumption has:

```yaml
id: h_metric_1
type: metric
claim: revenue means completed order amount minus refunds
source: llm_parse | user | docs | schema | history
confidence: 0.0..1.0
provenance: ...
dependencies: [...]
repair_operator: ...
```

Initial fault taxonomy:

1. **Metric** — wrong measure or formula
2. **Entity** — wrong business entity definition
3. **Time** — wrong date field, timezone, period, or fiscal mapping
4. **Grain** — wrong unit of aggregation
5. **Join** — wrong relationship/path/cardinality assumption
6. **Filter** — wrong inclusion/exclusion logic
7. **Value mapping** — wrong mapping from language to categorical/database values
8. **Business rule** — missing or stale external rule
9. **Null semantics** — incorrect behavior around NULL/missing values
10. **Deduplication** — wrong DISTINCT/key convention
11. **Ordering/top-k** — wrong ranking or tie convention
12. **Dialect/environment** — SQL behavior dependent on engine/dialect

The first paper should focus primarily on categories 1-10 and read-only analytical SQL.

### 4.3 Semantic plan

Assumptions compile into an explicit plan:

```yaml
metric:
  expression: net_revenue
entity:
  object: customer
  qualifier: enterprise
filters:
  - completed_orders_only
  - country = US
time:
  window: FY26_Q2
  comparison: FY26_Q1
grain:
  output: region
joins:
  - customers -> orders
```

Each plan node records which assumptions justify it.

### 4.4 Observations

Measurements generate observations \(o \in O\). Observation types include:

- schema/FK inspection
- column statistics or value samples
- lightweight diagnostic SQL
- candidate execution result
- generated or benchmark test result
- query-plan/cardinality observation
- business-document retrieval
- historical-query retrieval
- user clarification
- cross-paradigm verifier result

### 4.5 Conflicts

A conflict is a set

\[
C_j \subseteq H
\]

such that the current evidence implies the assumptions in \(C_j\) cannot all remain trusted simultaneously.

Example:

```text
C1 = {h_join_cardinality, h_grain}
C2 = {h_metric, h_refund_filter}
C3 = {h_time_scope, h_fiscal_calendar_rule}
```

Because LLM-generated evidence is noisy, each conflict also has:

- source reliability \(r_j\)
- evidence provenance
- deterministic/learned flag
- optional likelihood model

The initial training-free system should maintain both:

1. **hard conflicts** — produced by deterministic tests or explicit benchmark/user facts
2. **soft conflicts** — produced by probabilistic or LLM-supported evidence

### 4.6 Diagnosis

A diagnosis \(\Delta\) is a set of assumptions hypothesized to be faulty such that it intersects every relevant hard conflict.

For hard conflicts, minimal diagnoses correspond to minimal hitting sets.

For ranking, use a weighted score:

\[
Score(\Delta) =
\sum_{h_i \in \Delta} -\log P(fault(h_i))
+ \alpha |\Delta|
+ \beta \cdot SoftViolation(\Delta).
\]

Lower scores are preferred.

The system returns top-k diagnoses rather than forcing a single diagnosis too early.

---

## 5. Assumption graph construction

### 5.1 Graph structure

Define a typed directed graph

\[
G_A = (H, E_A)
\]

where nodes are assumptions and edges encode dependency or justification relations.

Example:

```text
h_metric_revenue
      |
      v
h_amount_column -----> h_refund_filter
      |
      v
plan.aggregate
      |
      v
SQL SUM(...)
```

Dependencies are important because a diagnosed upstream assumption should invalidate downstream plan components without forcing unrelated parts to be regenerated.

### 5.2 Construction stages

1. Parse the user request into semantic slots and uncertainty alternatives.
2. Ground slots into candidate schema/business concepts.
3. Generate a semantic plan.
4. Compile plan to SQL.
5. Align SQL fragments back to plan nodes and assumptions.
6. Record provenance and confidence for every edge.

### 5.3 Training-free extractor

Use structured LLM output constrained by a JSON schema. The LLM is not trusted to decide correctness; it only proposes the initial assumption graph and mappings.

Every assumption should be phrased as a falsifiable claim.

Bad:

```text
"revenue handling"
```

Good:

```text
"revenue = SUM(orders.amount) over status='completed' rows"
```

### 5.4 Oracle assumption graph for controlled experiments

For synthetic and perturbation-based experiments, construct ground-truth assumption graphs programmatically. This allows root-cause diagnosis metrics independent of LLM extraction quality.

This is crucial: the paper must separate **diagnosis quality** from **assumption extraction quality**.

---

## 6. Conflict-generation system

The conflict layer should be a bank of independent evidence producers.

### 6.1 Static SQL-plan consistency

Checks include:

- output grain implied by GROUP BY vs declared grain
- metric expression vs declared metric
- DISTINCT/key usage vs deduplication assumption
- date predicate vs declared time window
- table/column use vs schema grounding
- join graph vs declared path

### 6.2 Cardinality and join probes

Cheap diagnostic queries can estimate whether joins unexpectedly multiply rows.

Example probes:

```sql
SELECT COUNT(*) ...;
SELECT COUNT(DISTINCT customer_id) ...;
```

Large divergence provides evidence against grain/cardinality assumptions.

### 6.3 Execution and test evidence

A failed executable test is converted into a conflict over assumptions that can affect the tested behavior.

The mapping from test -> affected assumptions comes from semantic-plan dependency edges.

### 6.4 Query-plan evidence

EXPLAIN-derived signals can create conflicts for:

- unexpected join explosion
- missing selective predicate
- full scans inconsistent with intended narrow filter

Optimizer evidence should remain supporting evidence, not a correctness oracle.

### 6.5 Documentation and knowledge evidence

Retrieved knowledge can contradict assumptions such as metric/time/entity definitions.

A conflict should include both the assumption and the retrieved rule's provenance. Stale documents must not automatically override newer evidence.

### 6.6 User evidence

A user answer can create a near-hard constraint, subject to benchmark/user-simulator reliability assumptions.

### 6.7 Cross-paradigm evidence

DPC-style Python/Pandas or other independent executable formulations can contribute conflicts, but DiagSQL uses them to update fault hypotheses rather than only select a SQL candidate.

### 6.8 LLM contradiction proposer

A learned/LLM verifier may suggest a conflict only if it identifies:

- assumptions involved
- supporting observation
- expected contradiction
- confidence

Ungrounded prose criticism should not enter the diagnosis engine.

---

## 7. Diagnosis engine

### 7.1 V0: exact hard-conflict diagnosis

For small assumption graphs, compute top minimal hitting sets over hard conflicts.

Implementation choices:

- HS-tree / hitting-set tree
- branch-and-bound top-k hitting set
- integer linear programming / MaxSAT formulation

For the initial prototype, a branch-and-bound enumerator is sufficient because semantic assumption sets should usually be tens of nodes rather than thousands.

### 7.2 V1: weighted diagnosis

Assign priors to fault types and assumptions. Priors can depend on:

- LLM uncertainty
- source reliability
- historical fault frequency
- schema-link confidence
- whether a business rule was inferred or explicitly retrieved

Rank diagnoses by posterior-like cost while retaining hard-conflict consistency.

### 7.3 V2: learned diagnosis ranking

Train a ranker from diagnostic trajectories to estimate

\[
P(\Delta \mid G_A, O).
\]

This is optional for the first paper. The paper should be able to demonstrate the core contribution without requiring task-specific training.

### 7.4 Complexity control

Use:

- top-k diagnosis truncation
- maximum diagnosis cardinality
- conflict subsumption
- duplicate conflict removal
- dependency-based partitioning
- fault-type priors

If the diagnosis set explodes, the agent should prefer measurements that split large equivalence classes rather than enumerate all possibilities.

---

## 8. Active measurement selection

### 8.1 Action set

Candidate measurement actions:

```text
inspect_schema(table/column)
inspect_foreign_key(path)
sample_values(column)
run_probe(sql_template)
execute_candidate(sql)
explain_candidate(sql)
retrieve_business_rule(concept)
retrieve_historical_query(concept)
ask_user(question)
run_generated_test(test)
run_cross_paradigm_check(plan)
```

### 8.2 Diagnosis partition

A measurement is useful if possible outcomes partition the current leading diagnoses differently.

For diagnosis distribution \(P(\Delta)\), define expected information gain:

\[
IG(a) = H(\Delta) - \mathbb{E}_{o \sim P(o|a)}[H(\Delta|o,a)].
\]

### 8.3 Cost-aware utility

\[
U(a) = IG(a)
- \lambda_t C_{token}(a)
- \lambda_d C_{db}(a)
- \lambda_l C_{latency}(a)
- \lambda_u C_{user}(a)
- \lambda_r C_{risk}(a).
\]

The next measurement maximizes \(U(a)\).

### 8.4 Outcome prediction

Training-free outcome prediction can use:

1. deterministic simulation where possible
2. diagnosis partition rules
3. cheap database metadata
4. calibrated LLM estimates only for otherwise unmodeled outcomes

For example, if the two leading diagnoses disagree only on `revenue definition`, a user clarification or business-rule lookup has high expected value; inspecting an unrelated foreign key should have near-zero value.

### 8.5 Stopping

Stop diagnosis when any of these holds:

- posterior mass of top diagnosis exceeds threshold
- all leading diagnoses imply the same repair
- expected value of further measurement is below cost
- diagnostic budget is exhausted

This prevents over-interaction.

---

## 9. Semantic delta debugging

### 9.1 Goal

Given a failure predicate \(F(S)\) over an enabled assumption/plan subset \(S\), find a 1-minimal subset \(S^*\) that still induces the failure.

### 9.2 What can be minimized

- filters
- joins
- metric modifiers
- time clauses
- business-rule assumptions
- semantic-plan branches
- candidate repair changes

### 9.3 Failure predicates

Examples:

- benchmark executable test still fails
- candidate disagrees with trusted reference result
- invariant violation persists
- cross-paradigm disagreement persists
- ambiguity-sensitive output remains different

### 9.4 Role in DiagSQL

Delta debugging is not the main diagnosis engine. It is an auxiliary procedure for:

- shrinking broad conflicts
- generating compact explanations
- validating whether a diagnosis contains unnecessary assumptions
- producing controlled benchmark labels

### 9.5 Non-monotonicity caveat

SQL semantics can be non-monotonic with respect to removing plan fragments. Therefore DiagSQL should claim **1-minimality under the tested reduction operator**, not global minimal causality.

---

## 10. Diagnosis-constrained repair

### 10.1 Principle

Do not regenerate the complete query unless diagnosis is diffuse.

For diagnosis \(\Delta\), define affected plan closure

\[
Affect(\Delta) = \Delta \cup descendants_{G_A}(\Delta).
\]

Only this closure is editable by default.

### 10.2 Repair operators by fault type

**Metric**
- replace aggregate expression
- add/subtract business-rule components

**Entity**
- replace entity filter/definition

**Time**
- replace date field
- change calendar/fiscal boundary
- fix comparison window/timezone

**Grain**
- alter GROUP BY
- add DISTINCT/entity key

**Join**
- replace join path/key/type

**Filter/value mapping**
- update predicate or categorical normalization

**Business rule**
- inject retrieved rule into semantic plan

### 10.3 Repair modes

1. **Patch mode** — edit only diagnosed SQL/plan nodes.
2. **Local regenerate mode** — regenerate affected semantic subplan.
3. **Global regenerate fallback** — only when diagnosis entropy remains high or dependencies cover most of the plan.

### 10.4 Verification after repair

A repaired query must be re-run through the same evidence bank. The repair is accepted only if:

- original conflicts are resolved or explained
- no new hard conflict appears
- executable tests pass when available

---

## 11. Three implementation variants

### 11.1 Variant A — Logic-first training-free DiagSQL

**Recommended first implementation.**

Components:

- structured assumption extractor
- deterministic conflict bank
- exact/weighted hitting-set diagnosis
- rule-based active measurement utility
- diagnosis-constrained repair prompt

Advantages:

- easiest to interpret
- clearest causal ablation
- strongest connection to classical MBD
- no new training dataset required

Risk:

- conflict coverage may be limited

### 11.2 Variant B — Hybrid probabilistic DiagSQL

Adds:

- probabilistic fault priors
- soft conflict likelihoods
- calibrated action outcome model
- learned/LLM diagnosis ranker

Advantages:

- more robust to noisy enterprise evidence
- natural confidence/calibration story

Risk:

- harder attribution of gains

### 11.3 Variant C — Learned diagnostic policy

Treat diagnosis/measurement/repair as a sequential policy learned from traces.

This is a follow-up research direction, not MVP scope.

---

## 12. Evaluation design

### 12.1 Evaluation principle

Separate four capabilities:

1. assumption extraction
2. root-cause diagnosis
3. active measurement selection
4. repair

A system that repairs correctly by luck should not receive full diagnosis credit.

### 12.2 Controlled semantic-fault benchmark

Construct a benchmark by starting from validated semantic plans / SQL and injecting one or more typed semantic perturbations.

Fault injection families:

- metric substitution
- missing business filter
- calendar/fiscal swap
- wrong date column
- wrong grain
- DISTINCT removal
- join-path substitution
- join-type substitution
- value-map substitution
- stale business-rule substitution

Each episode stores:

- ground-truth fault assumptions
- affected SQL fragments
- valid discriminating measurements
- oracle repair

This benchmark gives precise localization labels.

### 12.3 BIRD-INTERACT adaptation

BIRD-INTERACT is especially useful because task data includes ambiguous user queries, explicit ambiguity metadata, unambiguous queries, external knowledge, and executable tests.

Construct diagnostic episodes by intentionally making a wrong ambiguity choice or masking relevant knowledge, then test whether DiagSQL identifies the assumption and chooses appropriate clarification/knowledge retrieval.

Primary use:

- semantic ambiguity diagnosis
- active user/document interaction

### 12.4 BIRD-CRITIC / SWE-SQL

Use as external-validity debugging benchmark.

Not every BIRD-CRITIC issue is a latent semantic-assumption fault. Map tasks into:

- compatible semantic/logic faults
- SQL-level runtime/dialect faults
- unsupported categories

Report category-specific results rather than forcing the whole benchmark into the framework.

### 12.5 BIRD / Spider / LiveSQLBench

Use validated SQL questions to create controlled perturbation episodes and measure end-to-end repair.

LiveSQLBench-style evolving business rules are a later extension for stale-rule diagnosis.

---

## 13. Baselines

### Repair baselines

1. Direct full-query regeneration from error/evidence
2. Execute-and-repair loop
3. DIN-SQL-style self-correction
4. generic ReAct debugging agent
5. Bird-Fixer/SWE-SQL-style debugging baseline where feasible
6. DeepEye-style targeted revision approximation

### Verification/selection baselines

7. LLM-as-a-Judge
8. self-consistency / execution-result voting
9. DPC-like candidate discrimination where applicable

### Diagnostic baselines

10. SQL-AST suspiciousness heuristic
11. LLM root-cause classification without explicit conflicts
12. random measurement
13. cheapest-first measurement
14. uncertainty-only measurement
15. oracle fault localization

The oracle localization baseline is important because it estimates the maximum repair gain available from perfect diagnosis.

---

## 14. Metrics

### 14.1 Diagnosis metrics

- fault assumption Top-1 accuracy
- Top-k recall
- mean reciprocal rank
- diagnosis set precision/recall/F1
- exact diagnosis match
- diagnosis cardinality
- calibration / Brier score for fault probabilities

### 14.2 Active diagnosis metrics

- measurements to correct diagnosis
- total measurement cost
- user interruptions
- DB calls
- token cost
- entropy reduction per unit cost
- area under diagnosis-accuracy-vs-cost curve

### 14.3 Repair metrics

- task/SQL repair success
- executable test pass rate
- semantic correctness where audited
- repair attempts to success
- tokens / DB cost / latency to repair
- unnecessary edit size outside oracle fault region

### 14.4 Explanation metrics

- size of semantic failure slice
- root-cause explanation faithfulness to injected fault
- evidence provenance coverage

---

## 15. Core experiments

### Experiment A — Does localization help repair?

Hold generator, prompt budget, and evidence constant.

Compare:

- direct regenerate
- evidence + regenerate
- diagnosis + constrained repair
- oracle diagnosis + constrained repair

If diagnosis does not close meaningful distance toward the oracle, the thesis weakens substantially.

### Experiment B — Does active measurement beat fixed evidence collection?

Compare:

- inspect everything
- fixed pipeline
- random measurement
- cheapest-first
- entropy-only
- cost-aware active diagnosis

Plot repair success and diagnosis accuracy against cumulative cost.

### Experiment C — Multi-fault diagnosis

Inject two and three interacting semantic faults.

Measure whether minimal hitting-set diagnosis provides gains over independent per-fault classification.

### Experiment D — Semantic delta debugging

Measure:

- conflict shrinkage
- explanation size
- repair search reduction
- extra DB/tool cost

### Experiment E — Noisy evidence

Corrupt or stale a fraction of retrieved business knowledge.

Compare hard-only, soft-weighted, and naive trust-all systems.

### Experiment F — Cross-model transfer

Keep diagnosis machinery fixed and swap SQL generator/LLM.

If gains survive model changes, the contribution is more likely to be architectural rather than model-specific.

---

## 16. Ablations

1. remove assumption graph; diagnose SQL clauses only
2. remove dependency edges
3. remove active measurement
4. replace hitting-set diagnosis with independent fault probabilities
5. remove conflict source reliability
6. remove semantic delta debugging
7. allow global regeneration instead of constrained repair
8. remove user clarification action
9. remove business-document evidence
10. remove execution/cardinality probes

The most important ablation is **semantic assumptions vs SQL-clause localization**. This directly tests the central novelty claim.

---

## 17. Statistical analysis

For paired repair outcomes, use paired bootstrap confidence intervals and McNemar-style paired significance tests where assumptions hold.

For cost distributions, report medians, quantiles, and bootstrap intervals because tool/LLM costs are typically heavy-tailed.

For ranking metrics, bootstrap at the task level.

Do not rely only on leaderboard point estimates.

---

## 18. Failure taxonomy for analysis

When DiagSQL fails, classify the failure into:

1. missing assumption — root cause never represented
2. wrong dependency — assumption graph maps evidence incorrectly
3. missing conflict — verifier/evidence bank fails to expose inconsistency
4. spurious conflict — noisy evidence misleads diagnosis
5. diagnosis explosion — too many equivalent fault sets
6. bad measurement model — selected action has low realized value
7. repair operator failure — root cause is known but repair cannot fix it
8. verification failure — repaired query is still silently wrong
9. benchmark ambiguity/annotation issue

This taxonomy is necessary to distinguish a diagnosis problem from a generation problem.

---

## 19. Scope and non-goals for first paper

### In scope

- read-only analytical SQL
- single- and multi-fault semantic errors
- explicit semantic assumption graphs
- hard + soft conflicts
- cost-aware active measurements
- constrained repair
- controlled benchmark + BIRD-INTERACT/BIRD-CRITIC evaluation

### Out of scope

- safe DML/DDL repair
- long-term semantic memory
- fully end-to-end RL policy
- organization-wide knowledge reconciliation
- formal proof of SQL semantic equivalence for the entire language

These can become follow-up papers.

---

## 20. Research risks and mitigation

### Risk 1 — Assumption extraction dominates everything

**Mitigation:** include oracle assumption-graph experiments and controlled programmatic graphs.

### Risk 2 — Hitting sets add complexity but not accuracy

**Mitigation:** compare against independent fault classification and single-fault tasks. Multi-fault gains must justify combinatorial diagnosis.

### Risk 3 — More measurements trivially improve repair

**Mitigation:** matched evidence and matched cost baselines; success-vs-cost curves.

### Risk 4 — Existing work appears too close

**Mitigation:** keep a strict novelty table covering:

- SQL fault localization
- SQL automatic repair
- database causality/diagnosis
- SWE-SQL/BIRD-CRITIC
- DeepEye-SQL
- DPC
- SpotIt/SpotIt+
- BIRD-INTERACT

The paper's distinct axis must remain latent semantic diagnosis + sequential measurement + constrained repair.

### Risk 5 — Synthetic fault injection is unrealistic

**Mitigation:** combine injected faults with BIRD-INTERACT ambiguity episodes and manually audit a stratified sample.

### Risk 6 — Conflict extraction is circular because the same LLM generates and judges

**Mitigation:** emphasize deterministic evidence, execution probes, user/benchmark facts, and cross-model/cross-paradigm evidence. Track conflict provenance explicitly.

---

## 21. Go / no-go criteria

Proceed toward a full paper if the MVP shows all of the following:

1. Diagnosis Top-3 recall is materially above simple LLM root-cause classification on controlled faults.
2. Diagnosis-constrained repair improves repair success or reduces cost relative to matched-evidence full regeneration.
3. Active measurement reaches comparable diagnosis/repair quality at lower cost than fixed evidence collection.
4. Gains persist across at least two generators/models or two benchmark families.
5. Semantic-assumption localization outperforms SQL-clause-only localization on semantic faults.

Strong paper signal:

- a clear success-vs-cost Pareto improvement
- large reduction in unnecessary edits
- interpretable root-cause traces
- meaningful oracle-localization gap closed

Stop or pivot if diagnosis adds computation but does not improve repair under matched evidence and matched budget.

---

## 22. Recommended MVP architecture

```text
Task Adapter
    |
    v
Assumption Extractor
    |
    v
AssumptionGraph + SemanticPlan
    |
    v
Initial SQL / failing SQL
    |
    v
Evidence Bank
    |-- static checks
    |-- execution tests
    |-- cardinality probes
    |-- schema/docs/user
    |-- optional cross-paradigm checker
    |
    v
Conflict Store
    |
    v
Diagnosis Engine
    |-- minimal hitting sets
    |-- weighted ranking
    |
    v
Measurement Planner
    |-- candidate action generation
    |-- diagnosis partition
    |-- expected IG - cost
    |
    +-------- loop until stop --------+
    |
    v
Constrained Repair
    |
    v
Verification + Trace
```

Keep every component independently testable. The diagnosis engine must not depend on an LLM API. The evidence bank should expose a common interface so new verifiers can be added without changing the core algorithm.

---

## 23. Proposed paper framing

### Working title

**DiagSQL: Diagnose Semantic Assumptions Before Repairing Text-to-SQL Agents**

Alternative:

**Before You Rewrite the Query: Active Semantic Diagnosis for Text-to-SQL Repair**

### Contribution structure

1. **Problem formulation:** latent semantic-assumption diagnosis for Text-to-SQL/Data-Agent failures.
2. **Method:** conflict-based top-k diagnosis plus cost-aware sequential measurement.
3. **Repair:** diagnosis-constrained semantic/SQL repair.
4. **Evaluation:** controlled root-cause benchmark plus realistic interactive/debugging benchmarks.
5. **Analysis:** diagnosis quality, repair gain, cost, multi-fault behavior, and failure taxonomy.

---

## 24. Key references for implementation and novelty audit

### Classical diagnosis

- Raymond Reiter. *A Theory of Diagnosis from First Principles*. Artificial Intelligence, 1987. DOI: 10.1016/0004-3702(87)90062-2.
- Johan de Kleer and Brian C. Williams. *Diagnosing Multiple Faults*. Artificial Intelligence, 1987. DOI: 10.1016/0004-3702(87)90063-4.
- Aimin Hou. *A Theory of Measurement in Diagnosis from First Principles*. Artificial Intelligence, 1994. DOI: 10.1016/0004-3702(94)90019-1.
- Alexander Feldman, Gregory Provan, Arjan van Gemund. *A Model-Based Active Testing Approach to Sequential Diagnosis*. JAIR, 2010 / arXiv:1401.3850.
- Patrick Rodler et al. *Inexpensive Cost-Optimized Measurement Proposal for Sequential Model-Based Diagnosis*. DX 2017.

### Delta debugging and repair localization

- Andreas Zeller and Ralf Hildebrandt. *Simplifying and Isolating Failure-Inducing Input*. IEEE TSE, 2002.
- Marko Vasic et al. *Neural Program Repair by Jointly Learning to Localize and Repair*. ICLR 2019 / arXiv:1904.01720.
- Tongtong Xu et al. *RESTORE: Retrospective Fault Localization Enhancing Automated Program Repair*. IEEE TSE, 2022.

### Databases and diagnosis

- Sarah R. Clark et al. *Localizing SQL Faults in Database Applications*.
- Y. Guo, N. Li, J. Offutt, A. Motro. *Automatically Repairing SQL Faults*. QRS 2018.
- Babak Salimi and Leopoldo Bertossi. *From Causes for Database Queries to Repairs and Model-Based Diagnosis and Back*. ICDT 2015.

### Text-to-SQL / data-agent frontier

- Wang et al. *Robust Text-to-SQL Generation with Execution-Guided Decoding*. arXiv:1807.03100.
- Pourreza and Rafiei. *DIN-SQL*. arXiv:2304.11015.
- Li et al. *SWE-SQL / BIRD-CRITIC*. arXiv:2506.18951.
- Li et al. *DeepEye-SQL*. arXiv:2510.17586.
- Huo et al. *BIRD-INTERACT*. ICLR 2026 / arXiv:2510.05318.
- Klopfenstein et al. *SpotIt*. ICLR 2026 / arXiv:2510.26840.
- Klopfenstein et al. *SpotIt+*. arXiv:2603.04334.
- Li et al. *DPC: Training-Free Text-to-SQL Candidate Selection via Dual-Paradigm Consistency*. ACL 2026.

---

## 25. Decision

Proceed with **Variant A: logic-first, training-free DiagSQL** as the first implementation and experimental scaffold.

The first milestone is intentionally narrow:

> Given an explicit assumption graph, one or more conflicts, and a fixed action catalog, compute ranked diagnoses, select a cost-aware discriminating measurement, and restrict repair to the diagnosed subgraph.

Only after this mechanism works in controlled episodes should the project add richer LLM-based assumption extraction, soft conflicts, learned priors, or benchmark-scale adapters.
