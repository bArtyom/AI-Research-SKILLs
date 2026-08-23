# Agentic Text-to-SQL: Research Ideas

This note expands the research landscape into concrete, falsifiable projects. The emphasis is on ideas that can become papers rather than only engineering improvements.

> For deliberately more distant cross-domain transfers, see [CROSS_DOMAIN_IDEAS.md](./CROSS_DOMAIN_IDEAS.md) and [EXOTIC_IDEA_ATLAS.md](./EXOTIC_IDEA_ATLAS.md). The latter adds 60 directions spanning physics, topology, information theory, cryptography, compilers, robotics, neuroscience, immunology, ecology, chemistry, economics, linguistics, category theory, operations research, and scientific methodology.

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

This turns schema linking into a policy problem where every observation has cost.

Potential observations:

- table summary
- column names/types
- foreign-key neighborhood
- sample values
- distinct-value sketches
- lineage
- documentation

---

## Idea 10 — Semantic Unit Tests Before SQL Generation

### Hypothesis

Generating expected semantic behaviors before generating SQL will improve reliability because the agent has a specification against which to test candidates.

### Example tests

For “customers whose spend increased year over year”:

- customers with no prior-year spend should not silently divide by zero
- cancelled orders should be excluded if business rules define revenue that way
- aggregation grain must be customer
- current and previous periods must have equal duration

The SQL generator must satisfy the test suite rather than merely imitate an answer format.

---

## Idea 11 — Disagreement Graph of SQL Candidates

### Hypothesis

Candidate diversity is useful only if the system understands *where* candidates disagree.

### Method

Generate multiple SQL candidates, then construct a disagreement graph where edges encode differences in:

- selected tables
- join paths
- predicates
- metric definitions
- aggregation grain
- time interpretation
- result behavior

Ask tools or users only about the highest-impact disagreement component.

### Contribution

Turn ensemble diversity into targeted information acquisition instead of majority voting.

---

## Idea 12 — SQL Agent Curriculum from Failure Taxonomy

### Hypothesis

Training on generic random SQL tasks wastes capacity. A curriculum generated from explicit semantic failure modes should improve agent robustness more efficiently.

### Failure dimensions

- ambiguous metrics
- hidden join duplication
- dirty categorical values
- wrong time grain
- slowly changing dimensions
- stale documentation
- contradictory business rules
- expensive scans
- incomplete permissions
- dialect mismatches

The curriculum generator increases difficulty only after the agent masters each failure family and their combinations.

---

## Recommended grouping

These twelve ideas form four coherent families:

1. **Adaptive interaction** — Ideas 1, 2, 7, 9, 11
2. **Verification and reliability** — Ideas 3, 4, 8, 10
3. **Long-lived agents** — Ideas 5, 12
4. **General data agents** — Idea 6

For research beyond these families, the newer [EXOTIC_IDEA_ATLAS.md](./EXOTIC_IDEA_ATLAS.md) deliberately reframes the problem through remote disciplines rather than extending the same agent architecture.
