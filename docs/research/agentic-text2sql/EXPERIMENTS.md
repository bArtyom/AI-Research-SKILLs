# Agentic Text-to-SQL Experiment Plan

## Research question

Can an adaptive data agent learn or infer **which interaction to perform next**—schema inspection, value probing, knowledge retrieval, clarification, SQL generation, execution, optimizer inspection, or verification—and thereby outperform fixed Text-to-SQL pipelines under the same compute and database budget?

## Primary hypothesis

At a matched cost budget, adaptive action selection improves task success over both direct generation and fixed retrieve-generate-repair pipelines, especially on tasks with incomplete context, large schemas, business knowledge, or ambiguity.

## Benchmark matrix

| Benchmark | Primary use | Important properties |
|---|---|---|
| BIRD | fast iteration and established comparison | large DBs, external knowledge, execution-based evaluation |
| Spider 2.0 | enterprise realism | huge schemas, multiple SQL dialects, long workflows |
| LiveSQLBench | hidden/live generalization | CRUD, hierarchical knowledge, industrial schemas, business-rule drift |
| BIRD-INTERACT | interaction policy | clarification, knowledge acquisition, multi-turn tasks |
| BIRD-CRITIC / SWE-SQL | debugging | diagnose and repair SQL failures |

Do not rely on a single leaderboard number. Recent benchmark auditing work argues that annotation errors can materially distort Text-to-SQL evaluation, so a small manually audited subset should be maintained for final claims.

## Systems to compare

### B0 — Direct generation

Question + schema context → SQL.

No tools except final execution.

### B1 — Retrieval pipeline

Schema retrieval → SQL generation → execution.

### B2 — Fixed repair pipeline

Schema retrieval → generation → execute → critic → repair → execute.

### B3 — Fixed multi-candidate pipeline

Retrieve → generate N candidates → execute / verify → select.

### B4 — Unconstrained ReAct agent

Same tool set as the proposed method, but no explicit uncertainty state or learned cost-sensitive routing.

### M1 — Adaptive heuristic agent

Explicit uncertainty dimensions and hand-coded routing thresholds.

### M2 — Learned router

Train an action policy from successful trajectories or preference pairs.

### M3 — Full adaptive agent

Learned routing + verifier bank + adaptive test-time compute allocation.

## Backbone control

Use the same foundation model for all main systems. Otherwise, gains from orchestration and gains from model strength cannot be separated.

A robust design evaluates at least:

- one strong closed or frontier model
- one capable open-weight model

The open-weight model is important for policy training and reproducibility.

## Tool budget

Normalize agent resources per task.

Example hard caps:

- 12 tool calls
- 4 SQL executions
- 2 optimizer calls
- 1 user clarification
- fixed token ceiling
- database scan/timeout ceiling

Also report unconstrained performance to estimate the upper bound.

## Metrics

### Correctness

- execution accuracy / task success
- test-suite accuracy where available
- manually audited semantic accuracy
- SQL validity rate

### Agent behavior

- number of schema calls
- number of data probes
- number of executions
- number of verifier calls
- clarification rate
- unnecessary clarification rate
- average trajectory length

### Cost

- input/output tokens
- wall-clock latency
- SQL execution time
- bytes or rows scanned
- optimizer-estimated cost

### Reliability

- calibration / Brier score
- selective accuracy at abstention thresholds
- silent semantic error rate
- recovery rate after an initial failure

### Safety for CRUD

- unsafe mutation rate
- policy violation rate
- rollback success
- unnecessary refusal rate

## Core experiment A — Does adaptation help?

Evaluate B0–B4 and M1–M3 on a stratified benchmark sample.

Strata:

- small vs large schema
- no external knowledge vs required business knowledge
- simple vs complex joins
- low vs high ambiguity
- clean vs dirty values

Expected result: direct generation remains competitive on simple tasks, while adaptive agents gain primarily on high-uncertainty strata.

That interaction is important. If the adaptive agent uses expensive tools on every easy task, the research thesis is weakened.

## Core experiment B — Cost-success Pareto frontier

For each system, sweep budgets:

- 2 / 4 / 8 / 12 tool calls
- 1 / 2 / 4 / 8 SQL candidates
- small / medium / large token budget

Plot task success against total normalized cost.

The key claim should be Pareto efficiency, not only maximal accuracy.

## Core experiment C — Tool value ablation

Remove one tool class at a time:

- no value sampling
- no documentation retrieval
- no `EXPLAIN`
- no semantic verifier
- no user clarification
- no memory

For each ablation, measure both overall loss and which task strata degrade.

This reveals whether the action policy has learned meaningful specialization.

## Core experiment D — Fixed vs learned routing

Train routing from trajectories.

Possible training data:

1. strong-agent rollouts
2. counterfactual action labels generated by replay
3. human-edited successful traces
4. benchmark gold information when available

A useful offline target is **marginal action value**:

`value(action) = expected correctness improvement - normalized action cost`

Compare:

- heuristics
- supervised next-action classification
- pairwise preference model
- contextual bandit
- offline RL

## Core experiment E — Clarification policy

Construct ambiguous tasks with two or more plausible interpretations.

Conditions:

1. no clarification allowed
2. always clarify
3. LLM decides freely
4. uncertainty threshold
5. information-gain policy

Metrics:

- semantic success
- questions per task
- useful-question precision
- regret vs oracle clarification policy

## Core experiment F — Counterexample-driven verification

For questions with multiple plausible SQL candidates:

1. produce candidate pair
2. detect semantic disagreement
3. generate a discriminating test / counterexample
4. execute test
5. select candidate

Compare against:

- LLM judge
- majority vote
- execution success only
- random candidate

Focus analysis on silent semantic errors where all candidates execute successfully.

## Core experiment G — Optimizer-in-the-loop

Record plan features for generated SQL:

- estimated cardinality at each join
- scan types
- filter selectivity
- join order
- estimated cost

Test whether these signals predict wrong SQL independently of LLM confidence.

Then use optimizer feedback during repair and measure:

- semantic accuracy
- efficiency
- number of repairs

A strong result would show that query-plan features provide complementary supervision to textual critics.

## Core experiment H — Drift-aware memory

Build episodic tasks with changing business semantics.

Example:

- episode 1: “revenue” includes shipping
- episode 2: same definition
- episode 3: policy changes; shipping is excluded

Compare:

- no memory
- naive persistent memory
- timestamped memory
- verification-aware memory

Metrics:

- reuse benefit before drift
- stale-memory error after drift
- recovery speed
- refresh cost

## Statistical analysis

Use paired evaluation because all systems answer the same instances.

Recommended reporting:

- bootstrap confidence intervals
- paired permutation tests for task success
- effect sizes by difficulty stratum
- cost-normalized success

Avoid presenting tiny leaderboard deltas without confidence intervals.

## Error taxonomy

Manually label a representative failure set:

1. intent misunderstanding
2. schema-linking error
3. business-rule omission
4. join error
5. aggregation error
6. temporal reasoning error
7. value grounding error
8. syntax/dialect error
9. execution/runtime error
10. verifier false positive
11. verifier false negative
12. premature stopping
13. unnecessary tool use
14. stale memory
15. unsafe operation

This taxonomy should be linked to agent trajectories so failures can be attributed to decisions rather than only final SQL.

## Minimal 6-week execution plan

### Week 1

- implement DB sandbox and tool interface
- build direct and fixed-pipeline baselines
- define trace schema

### Week 2

- implement structured belief state
- implement adaptive heuristic router
- add static verifier and execution verifier

### Week 3

- run BIRD subset
- collect successful and failed traces
- define tool-value labels

### Week 4

- train supervised router
- compare fixed vs adaptive under matched budgets

### Week 5

- add one distinctive research component: optimizer feedback or counterexample verifier
- run ablations

### Week 6

- audit evaluation examples
- perform statistical analysis
- produce figures and draft paper story

## Go / no-go criterion

Continue toward a full paper if the adaptive router shows at least one of the following robust effects:

- higher task success at equal total cost
- equal task success at materially lower cost
- large gains on high-uncertainty tasks with minimal overhead on easy tasks
- learned tool specialization that generalizes to unseen schemas or benchmark families

If none appears, pivot from routing to the strongest component-level finding (e.g. optimizer-based verification or counterexample-driven SQL testing).
