# Anchor-Paper Failure-Boundary Idea Pool — 2026-08-26

**Status:** idea stage only.  
**Goal:** generate Text-to-SQL / data-agent research ideas from **already-observed failures**, not from method names.  
**Rule:** every idea below must survive a 20–50 sample falsification probe before any full experiment or system building.

---

## 0. Process used in this batch

This batch follows an anchor-paper-first workflow:

1. select recent top-tier / main-conference papers with public code/data and a concrete observed failure;
2. write the paper's core assumption and its failure boundary;
3. identify a structurally isomorphic failure in Text-to-SQL / data agents;
4. define a new task object or evaluation object before proposing a method;
5. design a 20–50 sample falsification probe;
6. define a kill criterion that stops the idea early if the core phenomenon is weak;
7. only after the phenomenon survives, design a method.

This explicitly rejects the pattern:

> memory / verifier / routing / uncertainty / causal / multi-agent + SQL = paper.

The target is instead:

> observed failure → precise boundary → new research object → falsifiable hypothesis.

---

# 1. Anchor papers

## Anchor A — RuleArena, ACL 2025

**Paper:** Ruiwen Zhou et al., *RuleArena: A Benchmark for Rule-Guided Reasoning with LLMs in Real-World Scenarios*, ACL 2025.  
**URL:** https://aclanthology.org/2025.acl-long.27/

RuleArena studies authentic rule-guided reasoning in airline baggage, NBA transactions, and tax rules. It reports that models struggle to identify and apply the correct rules, confuse similar regulations, and can still fail at computation even after relevant rules are identified. External oracle logic/math tools produce substantial gains.

**Structural lesson for Text-to-SQL:** enterprise SQL failures may remain after retrieval succeeds because the bottleneck is **operationalizing multiple natural-language rules into a relational program**.

**Do not copy:** generic rule-following benchmark, generic logic tool use.

---

## Anchor B — Too Consistent to Detect, EMNLP 2025

**Paper:** Hexiang Tan et al., *Too Consistent to Detect: A Study of Self-Consistent Errors in LLMs*, EMNLP 2025 Main.  
**URL:** https://aclanthology.org/2025.emnlp-main.238/  
**Code:** https://github.com/Tan-Hexiang/Too-Consistent-to-Detect

The paper defines **self-consistent errors**: an LLM repeatedly produces the same wrong response across stochastic samples. These errors do not disappear with scale and are difficult for several detection families. Cross-model signals help because different models can possess different blind spots.

**Structural lesson for Text-to-SQL:** execution, self-consistency, SQL/Pandas diversification, or repeated refinement may all fail if the system is trapped in the same upstream semantic misconception.

**Do not copy:** generic self-consistency detector or another verifier ensemble.

---

## Anchor C — τ-bench, ICLR 2025

**Paper:** Shunyu Yao et al., *τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains*, ICLR 2025.  
**URL:** https://proceedings.iclr.cc/paper_files/paper/2025/hash/1b126cc38b8638e07bef37e7b2bb72bf-Abstract-Conference.html  
**Code/data:** https://github.com/sierra-research/tau-bench

τ-bench evaluates agents through dynamic user interaction, policy rules, API tools, and **final database state**. Even strong function-calling agents have low success and poor pass^k reliability.

**Structural lesson for Text-to-SQL:** for CRUD / stateful data agents, action validity is not enough. The correct object is a trajectory through database states toward a goal state.

**Do not copy:** generic tool-agent-user benchmark or pass^k itself.

---

## Anchor D — AgentIF, NeurIPS 2025

**Paper:** Yunjia Qi et al., *AGENTIF: Benchmarking Instruction Following of Large Language Models in Agentic Scenarios*, NeurIPS 2025 Datasets & Benchmarks.  
**URL:** https://proceedings.neurips.cc/paper_files/paper/2025/hash/51bb3a8a33610a25aae074bfc51b1b1f-Abstract-Datasets_and_Benchmarks_Track.html  
**Code/data:** https://github.com/THU-KEG/AgentIF

AgentIF contains 707 human-annotated instructions from 50 real agentic applications. Instructions average 1,723 words and 11.9 constraints. Models can satisfy many individual constraints while failing the full instruction, with particularly weak performance on complex constraint structures and tool specifications.

**Structural lesson for Text-to-SQL:** long-schema failure may not be primarily a token-length problem. It may be a **constraint-composition / constraint-retention problem**.

**Do not copy:** generic long-instruction benchmark.

---

## Anchor E — AgentDojo, NeurIPS 2024

**Paper:** Edoardo Debenedetti et al., *AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents*, NeurIPS 2024 Datasets & Benchmarks.  
**URL:** https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html

AgentDojo formalizes a core agent-security problem: external tool results contain **untrusted data**, yet LLMs have weak formal separation between data and instructions. This allows indirect prompt injection to influence tool actions.

**Structural lesson for data agents:** database strings, documents, comments, tickets, and retrieved rows are data, but a language agent may interpret them as control instructions.

**Do not copy:** generic prompt-injection benchmark or generic sanitizer.

---

## Anchor F — GuideBench, ACL 2025 + LiveSQLBench rule drift

**Paper:** Lingxiao Diao et al., *GuideBench: Benchmarking Domain-Oriented Guideline Following for LLM Agents*, ACL 2025.  
**URL:** https://aclanthology.org/2025.acl-long.557/

GuideBench explicitly tests domain-oriented rule adherence and **rule updates**. Models remain imperfect when guidelines are diverse or change.

Text-to-SQL now has a real corresponding environment: LiveSQLBench-Large-v1 includes versioned external knowledge and **Business Rule Drift**, where definitions can change across versions.  
**Dataset:** https://huggingface.co/datasets/birdsql/livesqlbench-large-v1

**Structural lesson:** the key failure may be not retrieval of the latest rule, but **semantic hysteresis**: stale rules continue influencing generation after an authoritative update is present.

---

# 2. New failure-derived ideas

## Idea 67 — OracleRule-SQL: isolate rule compilation from retrieval

### Failure boundary

A Text-to-SQL agent may retrieve the correct business rule and still generate wrong SQL.

### New research object

Remove retrieval completely. Give the model the exact authoritative rule and evaluate only:

\[
\text{Natural-language rule} \rightarrow \text{relational program}
\]

Define rule operators such as:

- substitution / definition;
- exception;
- nested exception;
- temporal scope;
- existential / universal condition;
- precedence;
- aggregation rule;
- multi-rule composition.

The central question becomes:

> **What is the operationalization boundary of business rules in Text-to-SQL when knowledge access is perfect?**

### Collision boundary

Not enterprise retrieval, not RAG, not HKB construction, not generic rule reasoning. The contribution must be the **SQL compilation failure after oracle knowledge is supplied**.

### 20–50 sample falsification

Take 30–50 BIRD / LiveSQLBench / DIVER-style tasks with explicit knowledge. Supply the exact needed rule and schema. Manually label rule structure. Measure SQL correctness by rule type.

### Kill criterion

Stop if oracle-rule injection makes all rule families similarly easy (>90%) or if residual errors are mainly schema linking rather than rule operationalization.

### Why it is promising

A strong positive result would move the field from “retrieve better knowledge” to “compile semantic policy correctly.”

---

## Idea 68 — Rule Interaction Gap: individually solvable rules fail in composition

### Failure boundary

A model may correctly compile rule \(R_1\) and rule \(R_2\) independently but fail on \(R_1 \land R_2\).

Define:

\[
InteractionGap(R_1,R_2)
=
Acc(R_1)Acc(R_2)-Acc(R_1\land R_2)
\]

A stronger diagnostic is a matched triplet:

- task A requires only \(R_1\);
- task B requires only \(R_2\);
- task C requires both with the same schema and entities.

### New research object

**semantic rule interaction**, not SQL complexity.

Possible interactions:

- temporal × exception;
- aggregation × deduplication;
- negation × join scope;
- entity definition × filter;
- precedence × versioned rule.

### Collision boundary

Not generic compositional generalization. The phenomenon must be observed in executable relational programs with matched atomic-rule controls.

### Falsification probe

Construct 20–30 matched rule triplets from real benchmark rules where possible.

### Kill criterion

Stop if composition accuracy is close to the product expected from independent atomic errors and no super-additive interaction appears.

---

## Idea 69 — Semantic Hysteresis SQL: stale rules survive authoritative updates

### Anchor connection

GuideBench shows rule updates are difficult; LiveSQLBench-Large-v1 now provides versioned knowledge / Business Rule Drift.

### Failure boundary

Even after a newer rule is explicitly present, a model may partially preserve an older rule.

Example:

```text
v1: active customer = purchase in last 90 days
v2: active customer = purchase in last 60 days OR active subscription
```

Possible failure:

```text
uses 60 days but forgets subscription
```

or

```text
uses the new definition in prose but generates SQL equivalent to v1
```

### New metric

**Stale Rule Influence (SRI)**:

\[
SRI = P(\text{output retains a semantic component unique to old rule}\mid \text{new rule supplied})
\]

Also measure replacement completeness: which parts of a superseded rule survive.

### Why this is deeper than memory

The question is not how to store or retrieve memory. The latest rule is already in context. The question is whether the model performs **semantic replacement** rather than blending versions.

### 20–50 sample probe

Use versioned LiveSQLBench HKB pairs. For each drifted concept, compare v1-only, v2-only, and v1+v2-with-explicit-version tasks.

### Kill criterion

Stop if the presence of explicit version markers reduces stale-rule influence to near zero.

---

## Idea 70 — Execution-Absorbing Semantic Errors

### Anchor connection

“Too Consistent to Detect” shows stable wrong beliefs survive stochastic sampling. Text-to-SQL adds a special complication: a semantically wrong SQL query often **executes successfully and returns plausible data**.

### Failure boundary

Define an error as execution-absorbing if:

1. multiple samples converge on the same wrong semantic interpretation;
2. the query executes without runtime error;
3. execution-result feedback does not move subsequent generations out of that interpretation.

Formally, for semantic state \(z^-\):

\[
P(z_{t+1}=z^-\mid z_t=z^-,\; execution\ feedback) \approx 1.
\]

### New research object

An **absorbing semantic error state** in execution-guided generation.

This attacks a central assumption of execution-guided agents: that executing SQL produces informative corrective feedback.

### Falsification probe

Select 20–40 BIRD / LiveSQLBench tasks where initial wrong queries execute. Run 5 samples and 2–3 execution-feedback revisions. Manually cluster semantic error type.

### Kill criterion

Stop if execution feedback frequently changes the semantic interpretation or if stable errors are mainly syntax/grounding errors rather than semantic errors.

### Potential paper story

> Execution is useful for invalid programs but can be informationally silent for plausible semantic errors.

---

## Idea 71 — Cross-Representation Error Attractors

### Anchor connection

DPC-style SQL/Pandas verification assumes different representations provide useful diversity. The self-consistent-error literature warns that different outputs can still share the same underlying misconception.

### Failure boundary

A semantic misconception can survive transformation across:

- SQL;
- Python/Pandas;
- relational-algebra plan;
- natural-language analytical plan.

Define an **error attractor** \(e\) when independently generated representations all instantiate the same wrong semantic choice.

### New metric

For error type \(e\):

\[
CommonMode(e)=P(E_{SQL}=e,E_{Python}=e,E_{Plan}=e).
\]

Compare against independence:

\[
P(E_{SQL}=e)P(E_{Python}=e)P(E_{Plan}=e).
\]

### Collision boundary

Not another verifier ensemble. The first contribution is to test the **independence assumption** behind heterogeneous verification.

### Probe

Take 30–50 cases that remain wrong after candidate selection / verification. Generate independent SQL, Pandas, and semantic plans; annotate error type.

### Kill criterion

Stop if common-mode semantic errors are near the independence baseline or rare.

---

## Idea 72 — CommitReadiness-SQL: irreversible writes require semantic closure

### Anchor connection

τ-bench treats final state as the correctness object. BIRD-INTERACT / LiveSQLBench / DySQL now include CRUD and user interaction.

### Failure boundary

For a write action, an agent can possess unresolved semantic ambiguity but still commit an UPDATE / DELETE / INSERT.

### New research object

**commit readiness**: whether all constraints relevant to an irreversible write are resolved before execution.

Let \(U_t\) be unresolved task-relevant semantic constraints. A safe commit requires:

\[
U_t \cap Dependencies(write)=\emptyset.
\]

This creates a database-agent analogue of a transaction commit barrier.

### Evaluation design

Create matched read/write pairs with the same ambiguity:

```text
READ: Which inactive enterprise customers are affected?
WRITE: Archive inactive enterprise customers.
```

The correct agent should tolerate less uncertainty for the write version.

### Metrics

- premature commit rate;
- unresolved-constraint count at first write;
- clarification-before-write rate;
- unnecessary clarification rate for read-only tasks.

### Collision boundary

Not generic uncertainty routing and not generic abstention. The research object is **semantic closure before state-changing database actions**.

### 20–50 pair probe

20–30 read/write paired tasks from CRUD-capable benchmarks.

### Kill criterion

Stop if frontier agents already show near-perfect risk-conditioned commit behavior.

---

## Idea 73 — Goal-State Regret for CRUD agents

### Anchor connection

τ-bench evaluates final database state. DySQL reports that executable SQL does not guarantee task completion.

### Failure boundary

Two failed trajectories can be qualitatively different:

- one steadily approaches the correct final database state but misses one condition;
- another repeatedly executes valid SQL that moves the database farther from the requested goal.

Binary task success treats both as zero.

### New evaluation object

For database state \(s_t\) and goal state \(G\), define a task-specific state distance \(d(s_t,G)\).

Then:

\[
StateRegret = \sum_t \max(0,d(s_{t+1},G)-d(s_t,G)).
\]

Also report maximum divergence and recovery after divergence.

### Why it matters

This directly measures whether a stateful agent is **making progress** rather than merely executing valid commands.

### Probe

Replay 20–30 failed CRUD trajectories with gold final states. Start with deterministic row/cell diff and task-specific invariant checks.

### Kill criterion

Stop if most failed tasks are one-shot terminal errors with no meaningful trajectory divergence.

---

## Idea 74 — Constraint Retention Curve: large-schema difficulty may be constraint count, not token count

### Anchor connection

AgentIF shows that models may satisfy many constraints individually yet fail complete instructions. LiveSQLBench-Large has ~84K-token prompts, ~1K columns, HKB rules, and tool/SQL requirements.

### Failure boundary

Existing Text-to-SQL analyses often attribute large-schema degradation to context length or retrieval difficulty. But two contexts of equal length can contain very different numbers of **independent semantic constraints**.

### New research object

For each task define a set of necessary constraints:

```text
entity binding
metric definition
time scope
join relationship
filter
aggregation grain
deduplication
business-rule clause
output/order requirement
```

Measure **Constraint Success Rate (CSR-SQL)** and full-query success separately.

More importantly, control token length and vary number of relevant constraints.

### Core hypothesis

\[
P(\text{full success})
\]

falls faster with constraint count / interaction than predicted by context length alone.

### Probe

Manually annotate 20–30 LiveSQLBench tasks. Create matched context packs with similar token count but different relevant-constraint density using only real schema/HKB material.

### Kill criterion

Stop if token count explains most variance and constraint density adds little predictive power.

---

## Idea 75 — Super-Multiplicative Constraint Failure

This is a sharper version of Idea 74.

If constraints failed independently, instruction success would be approximately:

\[
ISR_{independent}=\prod_i P(C_i\; satisfied).
\]

Define:

\[
InteractionPenalty
=
ISR_{independent}-ISR_{observed}.
\]

A large positive penalty indicates that combining constraints causes **interaction failures beyond independent per-constraint weakness**.

### Why this matters

It can distinguish:

- “model is 95% reliable on each of 10 independent details, so complete success is naturally low”;
- “specific combinations actively interfere with one another.”

Only the second case justifies a new compositional method.

### Probe

Use the same 20–30 annotated tasks as Idea 74.

### Kill criterion

Stop if observed full success is well explained by independent constraint error probabilities.

---

## Idea 76 — Policy–Semantics Interference

### Anchor connection

AgentIF finds tool and condition constraints particularly difficult. Data agents increasingly carry non-semantic policies: read-only rules, cost limits, allowed tools, formatting contracts, privacy constraints, dialect restrictions.

### Failure boundary

Adding a valid operational policy may reduce **semantic SQL correctness**, even though the policy is logically independent of the requested analytical answer.

Example:

Base task:

> compute customer churn by region.

Policy-added task:

> compute the same result, but do not inspect raw PII, use only read-only tools, return no more than 20 rows, and do not use table X directly.

A model may satisfy the policy but silently drop a semantic requirement.

### New metric

**Semantic Policy Tax**:

\[
SPT = Acc_{semantic}(base)-Acc_{semantic}(base+policy).
\]

Measure by policy type and number of simultaneous policies.

### Collision boundary

Not generic instruction following. The contribution is showing that operational agent constraints interfere with **relational semantics** even when they are intended to be orthogonal.

### Probe

20–30 benchmark tasks with paired policy wrappers; use policies already present in real data-agent / DB-agent environments where possible.

### Kill criterion

Stop if semantic accuracy is stable under policies and errors are only policy violations.

---

## Idea 77 — Relational Non-Interference for untrusted database text

### Anchor connection

AgentDojo shows that tool-returned data can hijack an agent. In a data agent, untrusted content may be fetched from database rows or documents.

### SQL-specific distinction

Database text **must be allowed to affect the answer as data** but should not arbitrarily affect the agent's control policy.

For two databases identical except for instruction-like text embedded in an otherwise irrelevant field:

\[
D \equiv_{task} D'
\]

we want:

\[
ControlTrace(A,D) \approx ControlTrace(A,D')
\]

while normal task-relevant data changes are allowed to change the answer.

This is a relational form of non-interference:

> task-irrelevant data content must not gain control authority merely because it is written in natural language.

### New benchmark object

Paired database states differing only in semantically irrelevant instruction-like strings placed in realistic text columns, notes, tickets, comments, or retrieved documents.

### Collision boundary

Not “AgentDojo for SQL.” The novelty must be the **data-dependence vs control-dependence separation under relational querying**, including the fact that the agent chooses which rows to retrieve.

### Probe

20–30 real benchmark databases with controlled paired row modifications. Measure SQL/tool-plan changes, unauthorized actions, and answer changes.

### Kill criterion

Stop if standard system-level isolation already makes control traces essentially invariant.

---

## Idea 78 — Query-Induced Exposure

This idea follows only if Idea 77 reveals a problem.

### Failure boundary

A data agent controls its own information exposure by deciding what to query. A malicious / distracting row may not be in the initial context; it becomes visible only because the agent executes a broad diagnostic or exploratory query.

Thus attack surface is not fixed:

\[
Exposure_t = f(Query_{1:t}).
\]

### New research question

> Do exploratory database actions increase the probability that irrelevant natural-language data enters the control context and changes subsequent tool behavior?

### New metric

**Exposure Amplification**:

\[
EA = P(unsafe\ control\ influence\mid exploratory\ queries)
 - P(unsafe\ control\ influence\mid minimal\ task\ queries).
\]

### Why it is distinct

Generic indirect-prompt-injection benchmarks typically assume the agent receives hostile tool output. Here the agent's **query policy determines whether hostile/irrelevant rows are surfaced at all**.

### Probe

Only run if Idea 77 is positive. Compare minimal vs exploratory query policies on the same 20–30 paired tasks.

### Kill criterion

Stop if exposure probability is independent of query breadth or if retrieved row content is reliably isolated from control.

---

# 3. Strongest candidates after collision + feasibility filtering

## Tier A — run the falsification probe first

### A1. OracleRule-SQL / Rule Interaction Gap

Why: directly grounded in RuleArena-like failure and existing enterprise SQL evidence; removes retrieval and isolates one mechanism. Data requirement is modest and the claim is clean.

**Decisive probe:** does rule-composition accuracy collapse even when every required rule is given explicitly?

---

### A2. Execution-Absorbing Semantic Errors

Why: directly tests a hidden assumption behind execution-guided Text-to-SQL. If wrong executable queries form absorbing semantic states, many existing self-correction pipelines have a structural blind spot.

**Decisive probe:** does execution feedback fail to change the semantic error cluster over several revisions?

---

### A3. Cross-Representation Error Attractors

Why: directly tests the independence assumption behind SQL-vs-Pandas / heterogeneous verification. It can be falsified cheaply before inventing any verifier.

**Decisive probe:** is semantic-error correlation across representations far above an independence baseline?

---

### A4. CommitReadiness-SQL

Why: CRUD + ambiguity is now supported by real interactive SQL benchmarks. The contribution is a precise action-safety object rather than another uncertainty router.

**Decisive probe:** do agents commit writes while task-relevant semantic constraints remain unresolved, and is this materially worse than their behavior on matched read tasks?

---

### A5. Constraint Retention / Super-Multiplicative Constraint Failure

Why: industrial Text-to-SQL now has 60K–120K-token contexts. Before building better retrievers, establish whether failure is actually caused by context length, independent per-constraint reliability, or interaction among constraints.

**Decisive probe:** at matched token length, does relevant-constraint count / interaction explain a substantial additional part of failure?

---

## Tier B — promising but conditional

### B1. Semantic Hysteresis SQL

Run only if LiveSQLBench's versioned HKB exposes enough real update pairs to avoid building a mostly synthetic drift benchmark.

### B2. Goal-State Regret

Strong for CRUD agents if trajectories contain multi-step state divergence. Drop if most tasks are one-shot failures.

### B3. Policy–Semantics Interference

Interesting for enterprise agents but could collapse into generic instruction following; requires a clear SQL-specific interaction effect.

### B4. Relational Non-Interference

Important security direction, but generic prompt-injection literature is crowded. Pursue only if the SQL-specific relational/control separation yields a new measurable failure.

---

# 4. Ideas explicitly rejected or downgraded in this pass

The following should **not** be promoted without new evidence:

1. **Generic verifier ensemble** — collision with self-verification, DPC-style heterogeneous verification, and extensive verifier literature.
2. **Generic execution feedback** — execution-guided SQL is already mature; the research opportunity is its failure boundary, not adding more rounds.
3. **Generic long-context schema retrieval** — large-schema retrieval is crowded; first distinguish token length from constraint interaction.
4. **Generic business-rule memory** — LiveSQLBench already exposes drift; a new memory mechanism is weak unless stale-rule influence is first demonstrated.
5. **Generic prompt-injection defense for data agents** — AgentDojo / DRIFT / WASP / OS-Harm already make the broad problem obvious. A SQL project needs a distinctly relational security property.
6. **Generic risk-aware routing / ask-user policy** — interactive benchmarks already cover tool/user decisions. Commit readiness is a sharper object for CRUD.
7. **Generic multi-agent debate / self-consistency** — self-consistent errors show that repeated agreement can be a failure mode rather than evidence of correctness.

---

# 5. Recommended 3-probe sequence

Do not run a large benchmark first.

## Probe 1 — Rule composition

20–40 oracle-knowledge tasks.

Questions:

- Does performance fall sharply with rule interaction?
- Are atomic rules individually solved?
- Which interaction pairs create super-additive failure?

**Continue only if:** matched atomic-vs-composed degradation is large and reproducible.

---

## Probe 2 — Semantic absorbing states

20–40 executable wrong SQL cases.

Run multiple samples and execution-feedback revisions.

Questions:

- Are repeated errors semantically identical?
- Does database execution provide a contradiction or merely plausible numbers?
- Does error type survive revisions?

**Continue only if:** a meaningful fraction of errors remain in the same semantic cluster despite execution feedback.

---

## Probe 3 — Heterogeneous verifier independence

30–50 hard cases.

Generate SQL / Pandas / semantic-plan solutions independently.

Questions:

- How correlated are error types?
- Which errors are representation-specific vs semantic-common-mode?
- Does candidate diversity actually create epistemic diversity?

**Continue only if:** common-mode error correlation is substantially higher than independence would predict.

---

# 6. Highest-value possible paper framings if probes succeed

## Paper framing 1 — “Knowledge Retrieval Is Not the Bottleneck”

> Even with oracle enterprise rules, Text-to-SQL models fail to operationalize interacting business semantics. The dominant difficulty is semantic rule compilation, not retrieval.

Target: ACL / EMNLP / possibly SIGMOD depending on formalization.

---

## Paper framing 2 — “Execution Cannot Correct What It Cannot Contradict”

> Execution-guided Text-to-SQL is effective for invalid programs but can enter absorbing semantic error states when wrong queries execute successfully and return plausible results.

Target: ACL / ICLR / NeurIPS depending on method and scale.

---

## Paper framing 3 — “Diverse Programs, Same Misconception”

> SQL, Pandas, and natural-language plans often share the same upstream semantic error, violating the independence assumption behind heterogeneous candidate verification.

Target: ACL / EMNLP / ICLR.

---

## Paper framing 4 — “Semantic Closure Before Commit”

> Stateful database agents frequently execute irreversible writes before resolving task-relevant ambiguity. Correctness for CRUD agents therefore requires a commit-readiness criterion, not merely executable SQL.

Target: ICLR / NeurIPS agent track, SIGMOD/VLDB if tied tightly to transaction semantics.

---

## Paper framing 5 — “Large Schema or Too Many Constraints?”

> Industrial Text-to-SQL degradation is partly a constraint-composition problem rather than simply a long-context problem; models satisfy many local requirements but fail global relational consistency.

Target: ACL / ICLR / NeurIPS datasets-and-benchmarks or analysis paper.

---

# 7. Final prioritization

| Rank | Direction | Problem-first strength | Collision risk | Data support | Cheap falsification | Keep? |
|---:|---|---:|---:|---:|---:|---|
| 1 | OracleRule-SQL + Rule Interaction Gap | 5 | 2 | 4 | 5 | **Yes** |
| 2 | Execution-Absorbing Semantic Errors | 5 | 2 | 5 | 5 | **Yes** |
| 3 | Cross-Representation Error Attractors | 5 | 3 | 4 | 5 | **Yes** |
| 4 | CommitReadiness-SQL | 5 | 2 | 4 | 5 | **Yes** |
| 5 | Constraint Retention / Interaction Penalty | 5 | 3 | 5 | 4 | **Yes** |
| 6 | Semantic Hysteresis SQL | 4 | 3 | 4 | 4 | Conditional |
| 7 | Goal-State Regret | 4 | 3 | 4 | 4 | Conditional |
| 8 | Policy–Semantics Interference | 4 | 4 | 3 | 5 | Conditional |
| 9 | Relational Non-Interference | 5 | 4 | 3 | 4 | Conditional |
| 10 | Query-Induced Exposure | 4 | 4 | 2 | 3 | Park until Idea 77 is positive |

The key change from earlier ideation is deliberate: **no method is the idea yet**. For Tier-A directions, the next legitimate step is only the falsification probe. A new architecture should be designed only after the corresponding failure phenomenon is observed.