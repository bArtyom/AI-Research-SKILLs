# AIDA-SQL Architecture

AIDA-SQL (Adaptive Interactive Data Agent for SQL) is a proposed research architecture for moving beyond fixed Text-to-SQL pipelines.

## Design objective

The agent should answer a data request by selecting the **minimum-cost sequence of actions that reduces semantic uncertainty enough to produce a verified answer**.

The architecture therefore separates four concerns:

1. **belief state** — what the agent currently knows and does not know
2. **action policy** — what to do next
3. **SQL synthesis** — how to realize a semantic plan as executable SQL
4. **verification** — how to falsify or confirm the candidate

## High-level loop

```text
User request
    |
    v
Intent + uncertainty parser
    |
    v
Belief state --------------------------------------------------+
    |                                                          |
    v                                                          |
Action policy                                                  |
    |                                                          |
    +--> inspect schema                                        |
    +--> retrieve business knowledge                           |
    +--> sample values                                         |
    +--> ask clarification                                     |
    +--> generate semantic plan                                |
    +--> compile SQL                                           |
    +--> execute probe                                         |
    +--> EXPLAIN / optimizer                                   |
    +--> verifier bank                                         |
    +--> generate alternative                                  |
    +--> stop                                                  |
    |                                                          |
    v                                                          |
Observation ----------------------------------------------------+
```

The loop terminates when the expected value of another action is lower than its cost or when a hard budget is reached.

## 1. Belief state

Rather than storing only conversation messages, maintain an explicit structured state.

```json
{
  "intent": {
    "entities": [],
    "metrics": [],
    "filters": [],
    "time_window": null,
    "ambiguities": []
  },
  "schema": {
    "known_tables": [],
    "candidate_tables": [],
    "known_joins": [],
    "unresolved_links": []
  },
  "knowledge": {
    "business_rules": [],
    "provenance": []
  },
  "candidates": [],
  "verification": {
    "passed": [],
    "failed": [],
    "open_risks": []
  },
  "uncertainty": {
    "intent": 0.0,
    "schema": 0.0,
    "semantics": 0.0,
    "execution": 0.0
  },
  "budget": {
    "tokens_left": 0,
    "tool_calls_left": 0,
    "db_cost_left": 0
  }
}
```

The important research choice is that uncertainty is factorized. A schema uncertainty should trigger different actions from a business-definition uncertainty.

## 2. Tool layer

### Schema tools

- `list_tables()`
- `describe_table(table)`
- `get_foreign_keys(table)`
- `search_schema(text)`
- `get_column_stats(table, column)`

### Data exploration tools

- `sample_values(table, column, k)`
- `count_distinct(table, column)`
- `run_probe(sql, limit, timeout)`

These should be rate-limited and preferably operate on a read-only replica.

### Knowledge tools

- `search_metric_catalog(query)`
- `search_business_docs(query)`
- `retrieve_prior_queries(query)`

Every returned item should carry provenance and freshness metadata.

### SQL tools

- `parse_sql(sql)`
- `execute_sql(sql)`
- `explain_sql(sql)`
- `estimate_cost(sql)`
- `transpile_sql(sql, dialect)`

### Verification tools

- `static_check(sql, intent)`
- `generate_invariants(intent)`
- `run_metamorphic_tests(sql)`
- `compare_candidates(sql_a, sql_b)`
- `generate_counterexample(sql_a, sql_b)`

### Interaction tool

- `ask_user(question, options, reason)`

The action policy should use this sparingly because user interruption is expensive.

## 3. Semantic plan intermediate representation

Direct SQL generation entangles semantic reasoning with dialect and syntax. AIDA-SQL should optionally produce a typed query graph first.

Example:

```yaml
metric:
  expression: sum(orders.revenue)
  alias: revenue
entity:
  group_by: customer.region
joins:
  - left: orders.customer_id
    right: customer.id
filters:
  - field: orders.status
    op: !=
    value: cancelled
time:
  field: orders.created_at
  range: previous_fiscal_quarter
comparison:
  type: quarter_over_quarter_growth
order:
  by: growth_rate
  direction: desc
limit: 10
```

This representation enables three independent checks:

1. natural language → semantic plan
2. semantic plan → schema bindings
3. semantic plan → SQL

A failure can therefore be localized rather than repaired blindly.

## 4. Action policy

### Baseline policy

A deterministic baseline is useful for ablations:

```text
if intent ambiguity high:
    ask user
else if schema uncertainty high:
    inspect schema
else if business-rule uncertainty high:
    retrieve knowledge
else if no candidate:
    generate plan + SQL
else if syntax/type failure:
    repair SQL
else if semantic verification weak:
    invoke verifier
else if optimizer anomaly:
    inspect plan / revise
else:
    stop
```

### Learned policy

The research model selects action `a_t` from state `s_t`:

`a_t ~ π(a | s_t)`

Reward can combine task success and cost:

`R = success - λ_token*C_token - λ_db*C_db - λ_latency*C_latency - λ_user*C_user - λ_risk*C_risk`

Training options:

- supervised imitation from successful traces
- DPO / preference optimization over alternative trajectories
- contextual bandits for tool routing
- offline RL using stored interaction traces
- online RL in sandbox databases

A particularly practical route is **trace distillation**: collect trajectories from a strong unconstrained agent, label which calls were actually useful, then train a smaller router to reproduce only high-value actions.

## 5. Candidate generation

AIDA-SQL should preserve diversity at the semantic-plan level.

Possible strategy:

1. generate 2–4 distinct semantic interpretations
2. bind each to schema
3. compile only plausible interpretations
4. verify candidates
5. allocate more compute only if the verifier cannot separate them

This is cheaper and more interpretable than generating 20 near-duplicate SQL strings.

## 6. Verifier bank

No single verifier is reliable. Use heterogeneous checks.

### Static

- valid identifiers
- join connectivity
- aggregation/grouping consistency
- suspicious Cartesian products
- missing filters
- data type compatibility

### Execution

- runtime success
- empty-result anomaly
- result cardinality
- timeout / scan cost

### Semantic

- intent-to-plan consistency
- plan-to-SQL consistency
- business-rule coverage

### Metamorphic

Examples:

- adding an impossible filter should return zero rows
- relaxing a monotonic filter should not reduce count
- equivalent date rewrites should preserve output
- redundant joins should not change results

### Differential

If two candidates disagree, identify the semantic difference and construct a discriminating test.

## 7. Optimizer feedback

The optimizer can act like a system-level critic.

Potential anomaly features:

- unexpectedly large estimated join cardinality
- sequential scan on a supposedly selective predicate
- missing partition pruning
- expensive sort before aggregation
- join order inconsistent with inferred relation structure

The agent can learn correlations between these features and semantic errors.

## 8. Memory

A persistent data agent benefits from organization-specific memory, but memory needs validity tracking.

Each item:

```yaml
statement: Revenue excludes refunded orders
source: metric_catalog://revenue/v4
valid_from: 2026-01-01
last_verified: 2026-08-20
scope: analytics.orders
confidence: 0.98
refresh_policy: weekly
```

At inference time, the agent chooses:

- reuse
- verify
- refresh
- ignore

This enables experiments on drift-aware memory.

## 9. Safety architecture

For read queries:

- read-only database credentials
- row and byte scan limits
- statement timeout
- allow-listed schemas

For write operations:

- classify mutation intent
- explicit permission check
- affected-row estimate
- transaction + savepoint
- dry-run / shadow table where possible
- pre/post invariants
- optional human approval
- rollback on verifier failure

Safety should be measured empirically rather than treated as a prompt-only property.

## 10. Observability and trace schema

Every episode should record:

```json
{
  "episode_id": "...",
  "question": "...",
  "actions": [
    {
      "type": "inspect_schema",
      "input": {},
      "output_summary": "...",
      "latency_ms": 0,
      "token_cost": 0,
      "db_cost": 0,
      "uncertainty_before": {},
      "uncertainty_after": {}
    }
  ],
  "final_sql": "...",
  "task_success": true,
  "verification": {},
  "total_cost": {}
}
```

This trace format is essential for policy-learning research because it allows retrospective estimation of which actions were useful.

## Minimal MVP

A first implementation can avoid RL and still test the central thesis.

### MVP components

- PostgreSQL or DuckDB sandbox
- schema search tool
- value sampling tool
- business-doc retriever
- SQL executor
- `EXPLAIN`
- static verifier
- LLM router with structured action output
- trace logger

### MVP experiment

Compare three systems on BIRD or a curated enterprise-like subset:

1. direct Text-to-SQL
2. fixed agent pipeline
3. adaptive action-selection agent

Hold the backbone model constant. Cap all systems at the same token and execution budget.

If the adaptive system achieves better cost-adjusted task success, the core research hypothesis is supported.
