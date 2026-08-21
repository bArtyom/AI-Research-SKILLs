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

It chooses among actions such as schema inspection, clarification, SQL generation, execution, query-plan inspection, verification, and stopping.

## Run

```bash
cd demos/agentic-text2sql-lab
python aida_lab.py
python benchmark.py
python gym.py
python -m unittest -v
```

No third-party dependencies are required.

## Single-episode benchmark

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

## Generated SQL Agent Gym

`gym.py` turns the toy case into generated episodes. Every seed creates a new database with randomized previous/current revenue and order counts plus a large cancelled-order distractor. The hidden user intent randomly chooses whether "growth" means revenue or order count.

On the checked 50-episode run:

```text
adaptive-uncertainty-aware:
  semantic_success_rate = 1.00
  internal_verifier_mean = 1.00
  mean_cost = 4.65
  mean_tool_calls = 6
  mean_user_interruptions = 1

fixed-no-clarification:
  semantic_success_rate = 0.48
  internal_verifier_mean = 1.00
  mean_cost = 2.65
  mean_tool_calls = 5
  mean_user_interruptions = 0
```

This is not intended as a scientific result; it is an executable proof of concept for the **accuracy–information–cost tradeoff** that a learned policy should optimize.

The most interesting observation is that the fixed pipeline's internal verifier remains perfect even when semantic success is near chance. A verifier cannot validate information the system never acquired.

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

A minimal executable environment with a read-only safety boundary.

### `ToyReasoner`

A drop-in placeholder. Replace with an API LLM, local code model, fine-tuned Text-to-SQL model, ensemble, or semantic-IR compiler.

### `VerifierBank`

Currently deterministic and intentionally incomplete. This should grow into a bank of independent verification channels.

### `AdaptivePolicy`

Currently a transparent heuristic baseline. The real research target is a learned controller.

### `gym.py`

A minimal environment generator. It is the first concrete step toward **SQL Agent Gym**: automatically generated data-agent episodes with hidden semantics and adversarial distractors.

## Why the toy benchmark is useful

It separates four notions that are often conflated:

- **syntactic correctness**: does the SQL parse?
- **execution correctness**: does it run?
- **local verification**: does it satisfy known invariants?
- **semantic correctness**: did it answer what the user actually meant?

A system can pass the first three while failing the fourth.

This motivates clarification, semantic memory, and value-of-information reasoning as first-class agent actions.

## Next implementation steps

### Stage 1 — Replace the toy reasoner

Define an LLM adapter with structured outputs for uncertainty estimates, clarification candidates, semantic plans, SQL candidates, and verifier claims while keeping the environment API unchanged.

### Stage 2 — Expand the tool space

Add value sampling, documentation retrieval, historical-query retrieval, `EXPLAIN ANALYZE`, candidate comparison, generated unit tests, counterexample synthesis, and rollback-safe write transactions.

### Stage 3 — Expand SQL Agent Gym

Generate episodes containing:

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

Then train an adversarial environment generator to discover failure cases automatically.

### Stage 4 — Add real benchmark adapters

Wrap BIRD, Spider 2.0, LiveSQLBench, or BIRD-INTERACT episodes behind the same world interface.

### Stage 5 — Learn the policy

Progress from:

1. heuristic policy
2. supervised imitation from successful trajectories
3. contextual bandit for next-action selection
4. offline RL over logged trajectories
5. online RL in generated SQL Agent Gym environments
6. adversarial co-training between environment generator and SQL agent

### Stage 6 — Value-of-information objective

For every possible action `a`, estimate:

```text
Q(a) = expected task-loss reduction - lambda * action_cost
```

This turns clarification, schema exploration, verification, compute allocation, and stopping into one decision problem.

See `docs/research/agentic-text2sql/MOONSHOTS.md` for the broader research program.
