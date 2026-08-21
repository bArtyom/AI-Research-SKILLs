# Agentic Text-to-SQL Lab

A tiny executable research scaffold for the **AIDA-SQL** idea: Text-to-SQL as adaptive decision-making under uncertainty and cost.

The demo is deliberately model-agnostic and uses only Python's standard library + SQLite. The LLM is represented by a replaceable `ToyReasoner`; the important artifact is the environment/policy contract.

## What this demonstrates

The toy task is intentionally ambiguous:

> Which regions grew fastest last quarter?

"Growth" could mean revenue or order count. A fixed SQL pipeline can produce executable, locally verified SQL while still choosing the wrong business meaning.

The adaptive policy explicitly tracks:

- schema uncertainty
- semantic uncertainty
- execution uncertainty
- safety risk
- tool-call cost
- database-call cost
- user-interruption cost

It chooses among actions such as:

- inspect schema
- ask user
- generate SQL
- execute SQL
- inspect the query plan
- run deterministic verifiers
- stop

## Run

```bash
cd demos/agentic-text2sql-lab
python aida_lab.py
```

Run the fixed-vs-adaptive comparison:

```bash
python benchmark.py
```

Run tests:

```bash
python -m unittest -v
```

No third-party dependencies are required.

## Expected benchmark behavior

The benchmark intentionally separates the agent's **internal verifier** from a hidden semantic oracle.

A typical run shows:

```text
fixed-no-clarification:
  internal verifier = 1.0
  hidden semantic oracle = 0.0
  top result = East, 0.0

adaptive-uncertainty-aware:
  internal verifier = 1.0
  hidden semantic oracle = 1.0
  top result = North, 1.0
```

This failure mode is the point: **execution and self-verification do not resolve underspecified user intent**.

The adaptive agent spends one extra interaction to resolve the ambiguity, then generates the revenue-growth query.

## Current architecture

```text
question
   |
   v
BeliefState
   |
   v
AdaptivePolicy
   |
   +--> inspect_schema ----+
   +--> ask_user ----------+
   +--> generate_sql ------+
   +--> execute_sql -------+--> observations --> BeliefState
   +--> explain_sql -------+
   +--> verify ------------+
   +--> stop

CostLedger tracks action cost throughout the episode.
```

### `BeliefState`

The state is explicit instead of being buried entirely inside an LLM context window. That makes policy learning and analysis easier.

### `SQLiteWorld`

A minimal executable environment. It already has a read-only safety boundary for the demo.

### `ToyReasoner`

A drop-in placeholder. Replace with:

- an API LLM
- a local code model
- a fine-tuned Text-to-SQL model
- an ensemble
- a semantic-IR compiler

### `VerifierBank`

Currently deterministic and intentionally incomplete. This should grow into a bank of independent verification channels.

### `AdaptivePolicy`

Currently a transparent heuristic baseline. The real research target is to replace this policy with a learned controller.

## Why the toy benchmark is useful

It captures a subtle but important distinction:

- **syntactic correctness**: does the SQL parse?
- **execution correctness**: does it run?
- **local verification**: does it satisfy known invariants?
- **semantic correctness**: did it answer what the user actually meant?

The fixed pipeline can pass the first three and fail the fourth.

This motivates clarification, semantic memory, and value-of-information reasoning as first-class agent actions.

## Next implementation steps

### Stage 1 — Replace the toy reasoner

Define an LLM adapter with structured outputs for:

- uncertainty estimates
- clarification candidates
- semantic plan
- SQL candidate
- verifier claims

Keep the environment API unchanged.

### Stage 2 — Add more tools

Add:

- column/value sampling
- documentation retrieval
- historical-query retrieval
- `EXPLAIN ANALYZE`
- candidate comparison
- generated unit tests
- counterexample synthesis
- rollback-safe write transactions

### Stage 3 — Add a real benchmark adapter

Wrap BIRD, Spider 2.0, LiveSQLBench, or BIRD-INTERACT episodes behind the same world interface.

### Stage 4 — Learn the policy

Start with simple methods before full RL:

1. heuristic policy
2. supervised imitation from successful trajectories
3. contextual bandit for next-action selection
4. offline RL over logged trajectories
5. online RL in generated SQL Agent Gym environments

### Stage 5 — Add a value-of-information objective

For every possible action `a`, estimate:

```text
Q(a) = expected task-loss reduction - lambda * action_cost
```

This turns clarification, schema exploration, verification, and stopping into a unified decision problem.

## Bolder extension: SQL Agent Gym

The current code is intentionally small enough to become the seed of a full environment generator.

A future `SQLAgentGym` could sample entire episodes containing:

- schema ambiguity
- dirty values
- stale business rules
- hidden many-to-many joins
- distractor tables
- permission constraints
- expensive queries
- broken dashboards
- temporal drift
- adversarial documentation

The environment generator and SQL agent could then co-evolve, producing an automatic curriculum of failure cases.

See `docs/research/agentic-text2sql/MOONSHOTS.md` for the broader research program.
