# Agentic Text-to-SQL Research Landscape (2026)

> Research notes for exploring Text-to-SQL, SQL agents, and the convergence toward general-purpose data agents. Prepared in August 2026.

## Executive thesis

Text-to-SQL is no longer best viewed as a one-shot translation problem. The frontier is shifting toward **interactive, tool-using, verifiable data agents** that can search schemas, inspect values, read business knowledge, execute probes, ask clarification questions, repair failures, and decide when they have enough evidence to stop.

Three signals make this shift especially clear:

1. **Realistic enterprise benchmarks remain far from solved.** Spider 2.0 reports only 17.0% task success for its o1-preview-based code-agent baseline, despite much higher performance on classic Spider and BIRD.
2. **Agentic evaluation is becoming explicit.** LiveSQLBench separates direct model generation from Agent mode and includes CRUD/management SQL, hierarchical knowledge, hidden/live releases, industrial-scale schemas, and business-rule drift. Its 2026 leaderboard still leaves substantial headroom.
3. **Interaction itself is now a research object.** BIRD-INTERACT evaluates conversational and open-ended agentic interaction, including clarification, knowledge retrieval, error recovery, and multi-turn CRUD tasks.

The central research opportunity is therefore not simply “generate better SQL.” It is:

> **Learn when, why, and how a data agent should interact with the database, documentation, optimizer, user, and its own verifiers under a limited cost budget.**

This turns Text-to-SQL into a compact environment for studying core agent questions: tool routing, uncertainty, planning, verification, memory, test-time scaling, reinforcement learning, safety, and human-agent interaction.

## Why this area is unusually attractive for agent research

Text-to-SQL has four properties that make it a strong agent laboratory:

- **Executable feedback.** SQL can be parsed, type-checked, executed, profiled, and compared against tests.
- **Partially observable environments.** The agent rarely sees the full schema, values, documentation, permissions, or business semantics at once.
- **Natural opportunities for active information gathering.** Schema lookup, value sampling, EXPLAIN, lightweight probes, and user clarification all reduce uncertainty.
- **Objective cost signals.** Token usage, database scans, latency, number of tool calls, query cost, and user interruptions can all be measured.

This makes it possible to go beyond “LLM-as-generator” toward **agent policy learning**.

## Evolution of the research paradigm

### Phase 1 — Single-shot semantic parsing

Classic Text-to-SQL focuses on mapping a natural-language question to a SQL string using a fixed schema context. Spider 1.0 is the canonical benchmark.

### Phase 2 — Decomposition and self-correction

Methods such as DIN-SQL decompose difficult questions into subproblems and add self-correction. The key idea is to use structured reasoning rather than one-pass decoding.

### Phase 3 — Retrieval, schema linking, and multi-agent pipelines

BIRD exposed large databases, dirty values, and external knowledge. Systems such as MAC-SQL and CHESS split work among schema/context retrieval, generation, and refinement components. The main problem becomes **context selection** rather than only generation.

### Phase 4 — Diverse generation and test-time compute

CHASE-SQL, XiYan-SQL, Agentar-Scale-SQL, and related systems exploit multiple reasoning paths, candidate ensembles, tournament selection, and test-time scaling. SQL correctness becomes a search-and-selection problem.

### Phase 5 — Software-engineering-style verification

DeepEye-SQL reframes Text-to-SQL as a software engineering process: grounding, N-version generation, deterministic checks, targeted revision, and confidence-aware selection. SWE-SQL/BIRD-CRITIC similarly expands the task from generation to diagnosing and fixing SQL failures.

### Phase 6 — Open-ended data agents

Spider 2.0, LiveSQLBench, BIRD-INTERACT, ReFoRCE, and FlexSQL push toward agents that repeatedly inspect and modify their environment instead of following a fixed pipeline. The core question becomes **adaptive interaction policy**.

## The most important unsolved problems

### 1. Tool-use policy is mostly hand-designed

Most agentic Text-to-SQL systems still hard-code workflows: retrieve schema, generate, execute, repair, select. A strong system should instead choose actions based on uncertainty and expected information gain.

Candidate actions include:

- list tables / inspect schema
- retrieve column descriptions
- search business documentation
- sample distinct values
- run a cheap diagnostic query
- run `EXPLAIN` / inspect query plan
- execute in a sandbox
- ask the user a clarification question
- generate another candidate
- invoke a specialized verifier
- stop and answer

**Research gap:** learn the orchestration policy rather than only the SQL generator.

### 2. Correctness is under-specified

Execution success is not semantic correctness. A wrong query can execute successfully and return plausible results.

Useful verification layers include:

- parser / syntax checks
- schema and type checks
- static logical checks
- generated unit tests
- metamorphic tests
- differential execution across alternative formulations
- result-distribution sanity checks
- invariant checking
- natural-language entailment between requested intent and query plan

**Research gap:** build a verifier bank that detects silent semantic errors, not just runtime failures.

### 3. Ambiguity should trigger interaction, not guessing

Real questions routinely omit definitions: “active customer,” “revenue,” “last quarter,” “top account,” “cancelled,” etc. A benchmark that requires a single immediate SQL query rewards confident guessing.

BIRD-INTERACT makes clarification measurable, but there is room for much more work on **information-gain-aware question asking**.

### 4. Database optimizers are an underused tool

Most systems use execution feedback but barely exploit optimizer feedback. `EXPLAIN`, estimated cardinalities, join order, scan type, predicate selectivity, and cost can reveal both semantic and efficiency problems.

**Research gap:** create agents that reason jointly over natural-language intent and query plans.

### 5. Organization semantics change over time

Production Text-to-SQL depends on an evolving semantic layer: metric definitions, aliases, business rules, permissions, and governance policies. LiveSQLBench’s business-rule drift points directly at this problem.

**Research gap:** memory that is useful but knows when it is stale.

### 6. Agent evaluation is too accuracy-centric

A production data agent should be measured on more than execution accuracy:

- task success
- semantic correctness
- database cost
- latency
- token cost
- number of tool calls
- number of user interruptions
- safety violations
- calibration / abstention quality
- robustness to schema and business-rule drift

This creates a natural multi-objective learning problem.

## Recommended research directions

The following directions appear especially promising for publishable work.

| Rank | Direction | Core novelty | Why now |
|---|---|---|---|
| 1 | **Adaptive Tool-Use SQL Agent** | Learn when to inspect schema, values, docs, optimizer, user, or verifier | Existing systems are strong but predominantly fixed-pipeline |
| 2 | **Uncertainty-Aware Clarification Agent** | Ask minimum-cost questions that maximally reduce SQL ambiguity | BIRD-INTERACT makes interactive evaluation realistic |
| 3 | **Optimizer-in-the-Loop Text-to-SQL** | Use `EXPLAIN`/cost/cardinality signals during reasoning and repair | Efficiency and enterprise deployment are increasingly important |
| 4 | **Counterexample-Driven SQL Verification** | Generate tests/invariants that falsify candidate SQL | Silent semantic errors remain a major failure mode |
| 5 | **Drift-Aware Semantic Memory** | Persist organizational knowledge while detecting stale rules | LiveSQLBench introduces business-rule drift |
| 6 | **Unified Generate-Debug-Operate Agent** | Treat generation, SQL debugging, and safe DB operations as one agent task | SWE-SQL and LiveSQLBench broaden the SQL task spectrum |
| 7 | **Learned Test-Time Scaling Controller** | Allocate candidate generation/refinement only where uncertainty warrants it | Agentar-Scale-SQL shows scaling helps, but cost control is open |
| 8 | **Safe Transactional Data Agent** | Permission-aware DML/DDL with dry-run, rollback, and invariant checks | CRUD benchmarks are emerging; safety is underexplored |

See [IDEAS.md](./IDEAS.md) for detailed hypotheses and experiment sketches.

## A concrete flagship idea

### AIDA-SQL: Adaptive Interactive Data Agent

AIDA-SQL is a proposed agent that maintains an explicit belief state over:

- user intent
- relevant schema
- required business rules
- candidate query plans
- semantic uncertainty
- execution risk
- expected cost of additional actions

At each step, it chooses one action from a tool set, then updates the state. The stopping rule is learned or calibrated: return SQL only when expected error is below a threshold relative to the cost of further interaction.

The most important design choice is that the system does **not** assume a fixed pipeline. A simple question may require one schema lookup and one generation call; a difficult question may trigger documentation retrieval, value exploration, clarification, multiple plans, test generation, and optimizer inspection.

This is a clean research framing because the contribution is not “another collection of agents.” It is an **adaptive decision policy over data-work actions**.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the proposed design.

## Suggested benchmark stack

A serious 2026 evaluation should avoid relying on one classic benchmark.

| Benchmark | What it tests | Role |
|---|---|---|
| BIRD | Large DBs, values, external knowledge, efficient SQL | Fast development / comparison |
| Spider 2.0 | Enterprise workflows, huge schemas, multiple dialects, long workflows | Realism / code-agent capability |
| LiveSQLBench | Live/hidden tasks, CRUD, HKB, industrial schemas, business-rule drift | Contamination resistance / generalization |
| BIRD-INTERACT | Clarification and open-ended interaction | Human-agent interaction policy |
| BIRD-CRITIC / SWE-SQL | Diagnose and repair real SQL issues | Debugging / self-repair |

Because recent work has identified serious annotation problems in major Text-to-SQL benchmarks, evaluation should also include manual auditing or executable test cases rather than treating leaderboard labels as unquestionable ground truth.

## What probably will not be sufficiently novel by itself

The following directions are useful engineering, but weak as standalone research contributions unless paired with a stronger hypothesis:

- adding more prompt templates
- assigning fixed roles to several agents without learning/adaptation
- majority voting over more SQL samples
- schema RAG with a generic vector store
- simple execute-and-repair loops
- replacing GPT-X with a newer foundation model
- reporting only Spider/BIRD execution accuracy

The frontier has already absorbed these ideas. A stronger paper should explain **why the agent chooses an action**, **what uncertainty it resolves**, and **how the behavior is verified or learned**.

## Research package

- [IDEAS.md](./IDEAS.md) — 12 concrete research ideas, ranked by novelty and feasibility
- [ARCHITECTURE.md](./ARCHITECTURE.md) — proposed AIDA-SQL architecture and agent loop
- [EXPERIMENTS.md](./EXPERIMENTS.md) — benchmark matrix, metrics, baselines, and staged experiments
- [REFERENCES.md](./REFERENCES.md) — annotated reading list

## Bottom line

The strongest direction is to stop treating Text-to-SQL as “natural language in, SQL out.” A more durable framing is:

> **Text-to-SQL is an interactive decision process in a partially observable data environment, where the agent must acquire evidence, synthesize executable programs, verify semantics, manage risk, and minimize total interaction cost.**

That framing naturally connects Text-to-SQL with agent learning, software engineering agents, database systems, reinforcement learning, and human-agent interaction — and gives a much larger research surface than another SQL generation pipeline.
