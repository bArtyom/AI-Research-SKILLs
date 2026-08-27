# Fresh Text-to-SQL / Data-Agent Idea Pool — 2026-08-26

**Status:** idea-stage only  
**Scope:** literature-grounded research ideation; no scientific experiments or performance claims  
**Branch:** `research-agentic-text2sql-2026`

## 1. Why this pool exists

This document records a fresh round of Text-to-SQL / SQL-Agent / Data-Agent ideation driven by 2026 developments rather than by incremental extension of an existing pipeline.

The main design rule for this round is:

> Do not treat “add another retriever / critic / verifier / agent / self-correction loop” as sufficient novelty. Prefer changes to the problem definition, correctness object, state representation, environment interface, or evaluation protocol.

Recent work makes several previously implicit assumptions questionable:

- SQL is becoming hybrid and partially stochastic because databases now expose AI-native functions.
- equivalent relational representations can lead LLMs to different answers even when the underlying data semantics are unchanged.
- business rules and schemas evolve over time.
- benchmark annotations themselves can be imperfect or ambiguous.
- harness/interface design can materially change agent capability without changing the backbone model.
- interactive data agents increasingly operate over writable databases, heterogeneous workspaces, and permission-constrained environments.

The pool below explores the research space created by these changes.

---

## 2. Idea family A — Epistemic SQL: is the answer identifiable at all?

### Idea 25 — CertainAnswer-SQL

When several semantic interpretations remain plausible, do not immediately guess one or ask the user. Execute the plausible interpretations and return only the part of the answer that is invariant across them.

Formally, for plausible query set `Q = {q1, ..., qk}`:

\[
CertainAnswer = \bigcap_{q_i \in Q} Answer(q_i)
\]

Research hypothesis: many ambiguous analytical questions may already have decision-relevant answers that are invariant across plausible interpretations, making clarification unnecessary.

### Idea 26 — Possible-Answer Envelope

Instead of forcing one interpretation, propagate semantic uncertainty into the final answer.

For categorical results, return the union of possible answers; for numeric analytics, return an interval or distribution induced by plausible semantic worlds.

This reframes ambiguity resolution into **ambiguity propagation**.

### Idea 27 — Semantic Condition Number

Define a sensitivity measure describing how strongly an analytical answer changes under small perturbations to wording, schema representation, business rules, or data assumptions.

A task can be syntactically simple yet semantically ill-conditioned.

Potential use:

- difficulty metric for benchmarks;
- trigger for clarification/abstention;
- robustness diagnostic for agents.

### Idea 28 — Identifiability Benchmark

Before scoring SQL generation, classify whether the information available to the agent is sufficient to identify a unique semantic program.

Possible task classes:

- identifiable;
- weakly identifiable;
- non-identifiable.

Evaluation actions become `solve / clarify / return certain answer / abstain`, rather than forcing every task into one SQL string.

### Idea 29 — Decision-Invariant SQL

The user may care about a downstream decision rather than exact numerical agreement.

If all plausible semantic interpretations induce the same action, ranking, or policy decision, the agent can stop even when the exact answer remains uncertain.

This changes the stopping criterion from semantic certainty to **decision sufficiency**.

---

## 3. Idea family B — GaugeSQL: invariance to equivalent relational representations

### Idea 30 — GaugeSQL

Treat alternative schemas that represent the same business world as different coordinate systems.

Desired property:

\[
Answer(u,S_1) = Answer(u,S_2)
\]

for semantically equivalent schemas `S1` and `S2`, even though their physical SQL programs differ.

Research question: can Text-to-SQL systems learn **representation invariance** rather than memorizing schema-specific lexical/structural shortcuts?

### Idea 31 — Commutative Text-to-SQL

Let `T_S` transform a schema and `T_Q` be the corresponding query transformation. Require generation to approximately commute with the schema transform:

\[
Generate(u,T_S(S)) \approx T_Q(Generate(u,S))
\]

This suggests an algebraic consistency loss rather than ordinary data augmentation.

### Idea 32 — Conceptual Late-Binding SQL

Do not bind the natural-language request directly to physical tables/columns.

First compile into a conceptual program containing entity, metric, dimension, relation, time and policy concepts. Only a final schema-specific compiler binds the conceptual plan to physical SQL.

This separates stable organizational semantics from changing storage layout.

### Idea 33 — Migration-Stable SQL

Generated analytical programs should survive schema migration.

Alongside SQL, store semantic dependencies, entity/metric bindings, key requirements, and schema-version constraints. After migration, re-bind the semantic program instead of re-solving the original natural-language question.

### Idea 34 — Schema Anti-Shortcut Training

Generate families of semantically equivalent schemas through renaming, normalization, denormalization, table splitting/merging, surrogate-key substitution, and irrelevant-schema injection.

Train/evaluate answer invariance across these transformations to suppress lexical and benchmark-specific schema shortcuts.

---

## 4. Idea family C — Stochastic SQL: AI functions turn queries into random programs

### Idea 35 — Stochastic SQL Semantics

AI-native SQL functions break the traditional assumption that a query deterministically maps a database snapshot to one relation.

Instead:

\[
q(D) \sim P(Y)
\]

Research target: formal and practical semantics for SQL queries containing stochastic AI operators.

### Idea 36 — Uncertainty Algebra

Attach uncertainty annotations to rows, predicates, aggregates, and AI-function outputs, then define how uncertainty composes through relational operators.

Final answers should expose both value and uncertainty source decomposition.

### Idea 37 — Risk-Sensitive Neural Query Optimizer

Optimize plans that mix deterministic relational operators and stochastic AI calls.

Possible objective:

\[
\min E[Cost] + \lambda CVaR_\alpha(Cost)
\]

subject to a probabilistic correctness constraint.

The optimizer chooses model size, number of calls, batching, caching, deterministic prefilters, and verification strategy.

### Idea 38 — Reproducible AI-SQL

Make AI-native analytical queries replayable by pinning database snapshot, model/version, prompt template, semantic-layer version, decoding configuration, and possibly random seed.

Define a reproducibility score for hybrid AI-SQL artifacts.

---

## 5. Idea family D — the data itself is uncertain

### Idea 39 — Quality-Aware SQL

Attach data-quality metadata such as completeness, freshness, source reliability, and entity-resolution confidence to columns/records.

Propagate these properties into answer confidence instead of pretending the database is perfect ground truth.

### Idea 40 — InfluenceSQL

Estimate which rows, groups, business rules, or assumptions have the largest influence on the final analytical conclusion.

The goal is not only to explain how SQL is written, but to explain whether the answer is dominated by fragile evidence.

### Idea 41 — Answer Stability Certificate

Produce a machine-readable robustness certificate describing which perturbations preserve the answer and which assumptions cause it to change.

Example perturbations:

- missing rows;
- alternative deduplication rules;
- plausible business-rule variants;
- alternative time semantics;
- noisy AI classifications.

### Idea 42 — Falsification Query

After producing a claim, create an adversarial analytical program whose objective is to find evidence that would refute it.

Search for confounders, Simpson's paradox, alternative slices, unstable time windows, small-sample effects, and outliers.

This reframes verification as **scientific falsification** rather than agreement with another critic.

---

## 6. Idea family E — transactional semantics for interactive writable agents

### Idea 43 — Intent Transaction

Treat a user's evolving intent as a transactional object.

The agent accumulates refinements such as exceptions, scope changes, and policy constraints before committing irreversible database actions.

Conceptual interface:

```text
BEGIN INTENT
REFINE
VALIDATE
COMMIT INTENT
```

### Idea 44 — Semantic Snapshot Isolation

Long-running tasks should execute against a joint snapshot:

\[
Snapshot = (DataVersion, SemanticVersion)
\]

Business definitions, policies, permissions, and data can all change during an agent trajectory. Mixing versions can silently corrupt analytical meaning.

### Idea 45 — ReversibleSQL Agent

Every write action must be paired with a compensating action, captured pre-state, affected-row estimate, postconditions, and rollback information before execution.

The safety predicate becomes `Recoverable(action)` rather than only `Allowed(action)`.

### Idea 46 — ShadowWorld DBA

Fork a shadow database/digital twin before risky remediation. Execute the candidate change in the shadow world, measure latency/load/locks/correctness/secondary effects, then decide whether to commit in production.

### Idea 47 — Mission-Safe Database Agent

Immediate safety is insufficient. An action should also preserve future feasibility of the overall maintenance objective.

Require that after action `a_t`, there still exists a continuation policy capable of reaching the mission goal.

---

## 7. Idea family F — evidence-carrying data agents

### Idea 48 — EvidenceCut-SQL

Given an answer supported by a large provenance DAG, find the smallest evidence subset sufficient to justify it.

\[
E^* = \arg\min_{E'} |E'| \quad s.t. \quad E' \models Answer
\]

This produces a compact audit certificate rather than an unreadable full trajectory.

### Idea 49 — CellProv Agent

Attach provenance to every output cell in a final table: source rows, query fragments, semantic assumptions, external rules, and snapshot version.

Potential metric: proportion of output cells with verified provenance.

### Idea 50 — Provenance Backpropagation

When the final answer is wrong, propagate blame backward over the execution/provenance DAG to semantic decisions, retrieved evidence, tools, and program fragments.

This creates structured credit assignment over **evidence and execution nodes**, not only tokens.

### Idea 51 — Claim-to-Query Alignment

Every natural-language claim in an analytical report should link to executable evidence: query fragment, result rows, assumptions, and data/semantic snapshot.

The result is a replayable analytical citation system.

---

## 8. Idea family G — Text-to-ApproxSQL

### Idea 52 — Text-to-ApproxSQL

Challenge the assumption that every user wants an exact result.

Generate an accuracy-budgeted analytical plan choosing between exact queries, sampling, sketches, approximate materializations, or approximate views.

### Idea 53 — Anytime SQL Agent

Return progressively refined answers under increasing computation budgets:

```text
500 ms  -> coarse estimate
2 s     -> narrower confidence interval
8 s     -> exact result
```

Stop when the marginal value of more computation falls below its cost.

### Idea 54 — User-Tolerance Query Planning

Infer or accept explicit user tolerances for accuracy, latency, and money, and feed them into query planning.

“Give me a quick estimate” and “this number goes into the quarterly filing” should induce fundamentally different plans.

---

## 9. Idea family H — automatically learning and maintaining the semantic layer

### Idea 55 — Semantic Layer Induction

Infer metrics, dimensions, canonical joins, entity definitions, filters, and temporal conventions from historical SQL, BI dashboards, dbt models, documentation, query logs, and user corrections.

Research target: turn organizational artifacts into an explicit semantic layer.

### Idea 56 — Semantic Layer Compression

Ask how small a semantic vocabulary is sufficient to explain most human analytical queries in an organization.

This connects semantic modeling with dictionary learning, grammar induction, and minimum-description-length ideas.

### Idea 57 — Semantic Layer Repair

Detect conflicting or stale metric/entity definitions across organizational artifacts, construct a conflict graph, and recommend merge/scope/version/deprecation operations.

The Data Agent becomes a maintainer of organizational semantics rather than only a consumer.

### Idea 58 — Relational Skill Induction

Compress repeated historical query patterns into typed, reusable program skills with preconditions, canonical joins, semantic assumptions, postconditions, and executable tests.

Future NL requests are solved by composing relational skills rather than retrieving whole historical SQL strings.

---

## 10. Idea family I — security: database content is untrusted input

### Idea 59 — Data-as-Instructions Firewall

Enforce a hard architectural distinction between control-channel instructions and data-channel content.

Database strings, documents, logs and comments must never silently become agent instructions.

### Idea 60 — TaintSQL Agent

Attach trust/taint labels to every external observation and propagate them through the agent execution graph.

Sensitive or destructive actions are blocked when their causal support depends on untrusted data.

### Idea 61 — Counterfactual Intent Attribution

Before a high-impact action, replay the reasoning with suspicious/untrusted observations removed or attenuated.

If the action disappears, flag it as likely induced by untrusted content rather than genuine user intent.

### Idea 62 — Adversarial Database Benchmark

Inject prompt-injection payloads into database rows, column descriptions, support tickets, PDFs, and external knowledge sources.

Measure unauthorized query changes, privacy leakage, policy violations, write actions, and final-answer corruption.

---

## 11. Idea family J — evaluation needs a new object

### Idea 63 — Metamorphic Text-to-SQL Evaluation

Replace dependence on a single gold SQL with semantic relations that must hold under controlled transformations.

Examples:

- schema renaming should not change the answer;
- adding irrelevant tables should not change the answer;
- semantics-preserving normalization/denormalization should preserve results;
- question paraphrases should preserve answers;
- controlled data transformations should induce predictable output transformations.

This directly addresses oracle uncertainty and benchmark annotation noise.

### Idea 64 — Harness-Normalized SQL Capability

A model's capability should be reported as a distribution over reasonable harnesses rather than one prompt/tool configuration.

Report both mean capability and harness sensitivity:

\[
E_H[Score(M,H)], \quad Var_H[Score(M,H)]
\]

Potential metric: **Harness Robustness Index**.

### Idea 65 — Database Apprenticeship Curve

Evaluate agents over a sequence of tasks from the same organization/database and measure whether accuracy improves and tool cost falls as the agent accumulates valid experience.

The key capability is learning to become a better analyst for a specific environment.

### Idea 66 — Semantic Unlearning Benchmark

After the agent has learned one organizational convention, change the metric definition, schema, policy, or canonical entity and measure how quickly stale knowledge stops influencing future behavior.

Potential metric: **semantic unlearning half-life**.

---

## 12. High-priority shortlist

The strongest ideas from this batch, judged by problem depth, distinctiveness, 2026 timing, and potential to become standalone research programs, are:

| Rank | Direction | Core reframing |
|---:|---|---|
| 1 | **CertainAnswer-SQL** | Do not resolve uncertainty that does not change the answer |
| 2 | **GaugeSQL / Commutative Text-to-SQL** | Learn the represented world, not its accidental schema coordinates |
| 3 | **Stochastic SQL Semantics** | AI-native SQL turns queries from deterministic functions into stochastic programs |
| 4 | **Semantic Snapshot Isolation** | Consistency must cover both data state and semantic/business-rule state |
| 5 | **Text-to-ApproxSQL** | Natural-language analytics should optimize user utility, not assume exactness |
| 6 | **EvidenceCut-SQL** | Trust should be supported by the smallest verifiable evidence certificate |
| 7 | **Semantic Layer Induction** | If semantic layers matter, learn them instead of assuming humans hand-author them |
| 8 | **ShadowWorld DBA** | Risky database-agent actions should be simulated in a digital twin first |
| 9 | **Identifiability Benchmark** | Some tasks are not solvable uniquely from the information given |
| 10 | **Uncertainty Algebra** | Data noise and stochastic AI operators require compositional uncertainty semantics |
| 11 | **Metamorphic Text-to-SQL Evaluation** | Evaluate semantic invariants rather than trusting a single gold program |
| 12 | **TaintSQL / Data-as-Instructions Firewall** | Data-agent security requires information-flow separation between data and control |

## 13. Three especially deep research programs

### Program A — Epistemic SQL

Combine:

- CertainAnswer-SQL
- Possible-Answer Envelope
- Semantic Condition Number
- Identifiability Benchmark
- Decision-Invariant SQL

Central question:

> When a natural-language analytical request admits multiple plausible semantic worlds, what can be answered safely without resolving all uncertainty?

This program could connect Text-to-SQL with incomplete databases, possible-world semantics, decision theory, abstention, and interactive clarification.

### Program B — Representation-Invariant SQL

Combine:

- GaugeSQL
- Commutative Text-to-SQL
- Conceptual Late Binding
- Migration-Stable SQL
- Schema Anti-Shortcut Training

Central question:

> Can a data agent reason about the underlying relational world independently of its accidental physical representation?

This program targets a more fundamental weakness than schema retrieval: representation sensitivity.

### Program C — Stochastic Relational Computing

Combine:

- Stochastic SQL Semantics
- Uncertainty Algebra
- Risk-Sensitive Neural Query Optimization
- Reproducible AI-SQL
- Quality-Aware SQL

Central question:

> What should relational semantics, optimization, reproducibility, and correctness mean once SQL operators themselves invoke uncertain AI models?

This program is particularly timely because AI-native database operators create a qualitatively new systems problem rather than another decoding variant.

---

## 14. Stopping point

This document intentionally stops at the idea/research-design boundary.

No claims are made that these directions improve benchmark accuracy. No model training, benchmark runs, hyperparameter tuning, or experimental comparisons are included here.

The next phase, if pursued separately on experimental infrastructure, should begin with novelty collision checks and minimal falsification experiments for the highest-priority directions rather than implementing the entire pool.
