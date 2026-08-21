# Agentic Text-to-SQL: Research Ideas

This note expands the research landscape into concrete, falsifiable projects. The emphasis is on ideas that can become papers rather than only engineering improvements.

## Idea 1 — Learned Tool Router for SQL Agents

### Hypothesis

A learned policy that selects information-gathering and verification tools based on uncertainty can outperform fixed agent pipelines at equal or lower cost.

### Action space

- inspect tables
- inspect columns / foreign keys
- retrieve documentation
- sample values
- search past successful queries
- generate SQL
- generate alternative plan
- execute
- `EXPLAIN`
- run verifier
- ask user
- stop

### Research contribution

Model Text-to-SQL as a finite-horizon decision process in which each tool call has cost and expected information gain.

### Experiments

Compare:

1. fixed retrieve → generate → execute → repair
2. ReAct-style unconstrained agent
3. heuristic uncertainty router
4. supervised learned router
5. contextual bandit / RL router

Measure success vs tool calls, DB cost, tokens, latency, and calibration.

---

## Idea 2 — Information-Gain Clarification for Ambiguous Analytics

### Hypothesis

A data agent that asks targeted clarification questions only when expected answer entropy reduction exceeds interruption cost will improve semantic accuracy with fewer user turns.

### Example

User: “Which regions grew fastest last quarter?”

Potential ambiguities:

- revenue vs order count vs GMV
- quarter relative to calendar or fiscal year
- absolute vs percentage growth
- region hierarchy

Instead of guessing, the agent estimates the downstream SQL distribution under plausible interpretations and asks the question that eliminates the most uncertainty.

### Novel angle

Evaluate **value of clarification**, not just question quality.

Metrics:

- execution accuracy after clarification
- semantic accuracy
- questions per task
- expected information gain
- regret relative to an oracle that knows when clarification is necessary

---

## Idea 3 — Optimizer-in-the-Loop Text-to-SQL

### Hypothesis

Query optimizer signals can expose semantic mistakes and guide efficient SQL generation beyond ordinary execution feedback.

### Agent tools

- `EXPLAIN`
- estimated rows
- scan type
- join order
- predicate selectivity
- query cost
- index usage

### Research questions

- Can cardinality surprises detect incorrect joins?
- Can high-cost plans identify missing predicates?
- Can plan comparison help select between semantically equivalent SQL candidates?
- Can optimizer feedback improve both correctness and efficiency jointly?

### Evaluation

Use BIRD’s efficiency-sensitive setting plus PostgreSQL/DuckDB synthetic workloads with known query equivalence.

---

## Idea 4 — Counterexample-Driven SQL Verification

### Hypothesis

The strongest verifier is not another LLM critic, but an agent that actively searches for database states or result-level counterexamples that distinguish competing SQL candidates.

### Core method

Given candidate queries `q1` and `q2`:

1. infer the semantic disagreement
2. generate adversarial rows or predicates that would make outputs differ
3. construct a temporary test fixture or constrained probe
4. execute both
5. retain or reject candidates based on the counterexample

This is analogous to property-based testing and counterexample-guided synthesis.

### Possible verifier families

- metamorphic relation generation
- synthetic row generation
- constraint-based test generation
- differential SQL execution
- natural-language invariant checks

---

## Idea 5 — Drift-Aware Semantic Memory

### Hypothesis

Long-lived SQL agents should remember organizational semantics, but a static memory creates systematic failures after metric definitions or business rules change.

### Memory contents

- metric definitions
- schema aliases
- join conventions
- fiscal calendar rules
- business filters
- user preferences
- successful query patterns

### Key novelty

Each memory item receives:

- provenance
- creation time
- observed support
- scope
- confidence
- expiry / drift score

Before reuse, the agent decides whether to trust, verify, or refresh the memory.

### Evaluation

Construct temporal benchmark episodes where schema and business definitions change. Measure adaptation speed and stale-memory failure rate.

---

## Idea 6 — Generate, Debug, and Operate with One Data Agent

### Hypothesis

SQL generation, debugging, and database operations are better modeled as a unified software-agent environment rather than separate tasks.

### Episode types

- answer an analytical question
- fix a broken SQL query
- optimize a slow query
- modify data safely
- migrate a schema
- validate a dashboard metric

### Why interesting

A single agent develops reusable skills: schema discovery, execution, verification, transaction safety, and rollback.

This would connect Text-to-SQL research to SWE agents and database administration agents.

---

## Idea 7 — Adaptive Test-Time Scaling Controller

### Hypothesis

Generating more SQL candidates helps difficult examples, but uniformly spending compute is inefficient. A controller can learn how much search to allocate per instance.

### Controller decisions

- number of candidate plans
- number of SQL realizations per plan
- number of verifier calls
- whether to use expensive models
- whether to ask the user

### Objective

Maximize:

`expected correctness - λ1 * tokens - λ2 * db_cost - λ3 * latency - λ4 * user_interruptions`

### Baselines

- fixed N-sampling
- self-consistency
- tournament selection
- uncertainty thresholding
- learned budget allocator

---

## Idea 8 — Safe Transactional SQL Agent

### Hypothesis

A data agent can perform DML/DDL safely if generation is wrapped in a transaction-aware verification protocol.

### Safety protocol

1. classify read vs write intent
2. estimate affected rows
3. check policy / permissions
4. generate preconditions
5. create dry-run or shadow execution
6. validate invariants
7. request approval when necessary
8. execute within transaction
9. post-check invariants
10. commit or rollback

### Research metrics

- task completion
- unsafe write rate
- unnecessary refusal rate
- rollback success
- policy compliance
- affected-row estimation error

---

## Idea 9 — Schema Exploration as Active Perception

### Hypothesis

Schema linking should be framed as sequential active perception rather than top-k retrieval.

The agent starts with a compressed catalog and repeatedly chooses which schema neighborhood to inspect next.

### Novelty

Use graph search or learned exploration over the schema graph, where each inspection reveals more nodes and metadata.

This matters for enterprise databases where passing the full schema to the model is impossible.

---

## Idea 10 — Query Plan as a Latent Reasoning Interface

### Hypothesis

Agents may reason more robustly when generating a typed relational plan before SQL rather than directly producing SQL tokens.

### Intermediate representation

A compact relational algebra / query graph:

- entities
- joins
- filters
- aggregations
- grouping
- ordering
- temporal constraints
- business-rule annotations

The agent can verify this graph independently from SQL syntax and compile it into multiple dialects.

### Research question

Does a plan representation improve cross-dialect transfer and semantic debugging?

---

## Idea 11 — Multi-Agent Debate over Semantics, Not SQL Strings

### Problem with ordinary multi-agent SQL

Multiple agents often just generate multiple SQL strings and vote. This creates correlated errors.

### Alternative

Assign agents to produce competing **semantic interpretations**:

- intent analyst
- schema mapper
- metric-definition specialist
- temporal reasoning specialist
- query-plan critic

Only after disagreements are resolved is SQL compiled.

### Hypothesis

Diversity at the semantic layer produces more useful disagreement than diversity at token generation.

---

## Idea 12 — Text-to-SQL as an Agent Curriculum Environment

### Hypothesis

SQL environments can provide a scalable curriculum for training general tool-using agents because rewards are executable and tasks naturally range from simple to long-horizon.

### Curriculum

1. single-table selection
2. joins
3. aggregation
4. nested queries
5. external business rules
6. hidden schema discovery
7. ambiguity / clarification
8. debugging
9. optimization
10. transactional operations

### Broader significance

The goal is not merely a better SQL agent. It is to use databases as a controlled environment for studying agentic reasoning, planning, and verification.

---

# Recommended priority

For a 2–4 month research project, prioritize:

1. **Learned Tool Router** — strongest agentic framing and manageable implementation.
2. **Counterexample-Driven Verification** — technically distinctive and easy to ablate.
3. **Optimizer-in-the-Loop** — strong systems + LLM crossover.
4. **Information-Gain Clarification** — high novelty, but evaluation requires interactive data.

For a larger 6–12 month effort, combine them into a unified adaptive data agent and train the orchestration policy end-to-end.
