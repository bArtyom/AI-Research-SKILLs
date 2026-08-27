# Moonshots: Beyond Text-to-SQL

This document intentionally pushes past incremental Text-to-SQL work. The goal is to identify research programs that could redefine the problem rather than merely improve leaderboard accuracy.

> For an even broader set of 60 remote cross-domain transfers, see [EXOTIC_IDEA_ATLAS.md](./EXOTIC_IDEA_ATLAS.md).

## 1. The Database Is the Agent's World Model

Today a database is treated as a tool. A more radical framing is to treat it as the **external world state** of an embodied reasoning agent.

The agent observes only fragments of this world through queries, schema inspection, statistics, plans, documentation, and user responses. Every SQL statement is an experiment on the world.

This suggests a POMDP formulation:

- hidden state: true organizational semantics + data state + user intent
- observations: schema, samples, query results, errors, query plans, docs
- actions: inspect, retrieve, query, clarify, modify, verify, stop
- reward: task utility minus compute, DB, latency, safety, and interruption cost

Text-to-SQL then becomes a benchmark for **active epistemic agents** rather than semantic parsers.

## 2. SQL Agent Gym: A Reinforcement-Learning Environment for Data Work

Build a Gym-style environment where agents learn data work by interacting with thousands of generated databases and tasks.

Episodes would include:

- analytical questions
- ambiguous business questions
- broken queries
- slow queries
- schema migrations
- permission-restricted tasks
- data quality incidents
- changing metric definitions
- adversarial or misleading documentation

Rewards could combine semantic correctness, execution cost, safety, and information acquisition cost.

A sufficiently rich SQL Agent Gym could become the data-agent analogue of software-engineering agent benchmarks.

## 3. Learned Value of Information

Instead of prompting an LLM to "think step by step," train an agent to estimate the **value of one more observation**.

Before each action, estimate:

`VOI(action) = expected reduction in task loss - action cost`

The agent should learn that:

- inspecting a foreign key can be more valuable than generating another candidate
- asking one clarification can dominate 20 self-consistency samples
- an `EXPLAIN` call can cheaply eliminate a structurally wrong join
- sometimes the best next action is to stop

This directly attacks wasteful test-time scaling.

## 4. Counterexample-Guided SQL Synthesis

Move from generate-and-judge to **generate-and-falsify**.

Given several plausible SQL programs, the agent searches for a counterexample that makes their semantics diverge. It can synthesize tiny temporary tables, adversarial rows, or metamorphic transformations.

Loop:

1. generate hypotheses
2. identify semantic disagreement
3. synthesize discriminating database state
4. execute candidates
5. eliminate inconsistent programs
6. repeat until one equivalence class survives

This is close to CEGIS and program synthesis, but with natural-language intent as the specification.

## 5. A Query Plan Critic That Reasons Over Optimizer Internals

The database optimizer contains a highly structured model of query behavior. Today SQL agents mostly ignore it.

Train a critic over:

- logical plans
- physical plans
- estimated vs actual cardinalities
- join algorithms
- predicate pushdown
- index use
- scan volume
- cost estimates

A model could learn patterns such as "this plan is suspicious because the join explodes cardinality before aggregation" and use them to repair both correctness and efficiency.

The deeper idea is to make the optimizer a **second reasoning system** that cross-examines the LLM.

## 6. Semantic Compilation Instead of SQL Generation

Stop generating SQL directly.

Compile natural language into an intermediate semantic representation containing:

- entities
- metrics
- dimensions
- filters
- temporal scopes
- grain
- joins
- aggregation semantics
- business-rule provenance

Then lower this IR into SQL dialects.

The novelty is not the IR itself; it is making the IR **inspectable, editable, verifiable, and persistent across turns**. The user and agent can negotiate semantics before SQL exists.

This could unify analytics agents with semantic layers such as dbt metrics and BI systems.

## 7. Query Programs as Proof-Carrying Artifacts

Require every generated SQL query to ship with a compact correctness certificate:

- which user phrase maps to which predicate
- why each table is necessary
- why each join is valid
- expected result grain
- invariants that should hold
- provenance for business definitions
- confidence and unresolved ambiguities

The query becomes a **proof-carrying program** rather than opaque code.

A verifier can reject SQL whose proof does not match execution structure.

## 8. Self-Evolving Organizational Semantic Memory

A production data agent should gradually learn an organization's private language:

- "bookings"
- "ARR"
- "active account"
- "qualified lead"
- fiscal calendars
- canonical joins
- dashboard conventions

But memory should not be static. Every fact needs provenance, scope, support, expiry, contradiction tracking, and refresh policies.

The moonshot is an agent that develops a **living semantic model of the company** while detecting when that model becomes stale.

## 9. Data-Agent Society: Specialized Agents with a Market for Compute

Instead of a fixed multi-agent team, create a market of specialist agents:

- schema archaeologist
- business-semantics retriever
- SQL synthesizer
- optimizer critic
- test generator
- privacy auditor
- transaction guardian
- result skeptic

Each specialist bids for the right to consume compute based on expected utility. A controller allocates budget dynamically.

This converts multi-agent orchestration into an economics / mechanism-design problem rather than a static role prompt.

## 10. Adversarial Databases That Co-Evolve With the Agent

Train a second agent whose job is to construct databases and schemas that expose weaknesses in the SQL agent.

The adversary can create:

- misleading column names
- near-duplicate tables
- hidden many-to-many joins
- null traps
- temporal edge cases
- inconsistent categorical values
- Simpson's paradox setups
- slowly changing dimensions
- metric-definition conflicts

The solver and environment generator co-evolve, producing an automatic curriculum of hard semantic cases.

## 11. Synthetic Organizations, Not Synthetic Questions

Most synthetic Text-to-SQL work generates more questions. A more ambitious direction is to generate entire **synthetic organizations**:

- schema history
- business docs
- dashboards
- metric definitions
- Slack-like decisions
- data quality incidents
- access-control policies
- historical queries
- organizational jargon

Then evaluate whether an agent can become competent inside that organization over weeks of simulated time.

This would test long-horizon memory and adaptation instead of isolated query accuracy.

## 12. Time-Traveling Data Agents

Give the agent a temporal environment where schemas and business rules evolve.

At time `t1`, "active customer" means one thing. At `t2`, finance changes the definition. At `t3`, a dashboard is migrated and the old definition remains in stale documentation.

Research questions:

- Can the agent infer which knowledge was valid at query time?
- Can it avoid contaminating historical analyses with current rules?
- Can it maintain temporally scoped memory?

This is a much harder and more realistic version of semantic drift.

## 13. Autonomous Metric Discovery

Reverse the usual direction. Instead of users always specifying metrics, let the agent discover candidate metrics and relationships worth tracking.

The agent searches for stable, predictive, actionable abstractions over raw tables and proposes semantic definitions together with executable SQL.

This blends:

- automated analytics
- representation learning
- causal discovery
- metric design
- data-product creation

A strong system could become an autonomous analytics scientist rather than a query interface.

## 14. Causal Text-to-SQL

Many business questions sound descriptive but are actually causal:

- "Did the promotion increase retention?"
- "Which campaign drove revenue?"
- "What caused churn to rise?"

A normal SQL generator will happily answer these with correlations.

A causal data agent should detect causal intent, refuse invalid identification, search for treatment/outcome/confounder structure, and produce either a defensible estimand or a precise statement of what cannot be inferred.

This would connect Text-to-SQL with causal inference rather than only database querying.

## 15. Privacy-Preserving Epistemic Agents

A data agent should reason not only about what it can query, but what it **should learn**.

Imagine an agent with a privacy budget that must choose observations while respecting row-level policies, differential-privacy constraints, and inference risks.

The action policy becomes:

> Which observation maximizes information gain about the task while minimizing information exposure?

This is a clean intersection between agentic reasoning, databases, and privacy.

## 16. SQL as a Universal Tool Language for Agents

SQL is increasingly available over more than relational tables: logs, vector stores, lakehouses, graph extensions, observability systems, and embedded analytics engines.

A general agent could use SQL as a common intermediate tool language across heterogeneous systems.

Research question:

> Can a single learned query-planning policy transfer across relational DBs, dataframes, log systems, graph extensions, and vector-search SQL dialects?

If yes, Text-to-SQL becomes a route toward general tool-use transfer.

## 17. World-Model Pretraining From Query Histories

Organizations contain millions of historical queries. These are traces of how humans understand the database.

Instead of merely retrieving similar SQL, pretrain a model to learn:

- latent schema neighborhoods
- canonical joins
- metric semantics
- analyst workflows
- query refinement patterns
- typical error corrections

The model would learn a **database-specific world model** from query trajectories before seeing a user's current question.

## 18. SQL Agent Neurosymbolic Search

Combine three systems explicitly:

1. an LLM proposes semantic hypotheses
2. a symbolic engine enumerates or constrains valid SQL structures
3. execution and counterexamples prune the search

Rather than having the LLM emit an entire program, use it to shape a constrained search distribution.

This could dramatically improve reliability on compositional queries where free-form generation fails.

## 19. The Agent Should Learn When Not to Use SQL

Some questions should be answered by:

- reading documentation
- asking the user
- running statistical analysis
- writing Python
- launching a causal workflow
- using a vector retriever
- refusing due to insufficient evidence

A mature data agent routes between SQL and other computational tools. The research task becomes **modality selection for data reasoning**, not Text-to-SQL alone.

## 20. Autonomous Data Researcher

The end-state is an agent that receives a vague objective such as:

> "Figure out why enterprise retention weakened and propose the most likely drivers."

It then autonomously:

1. discovers relevant datasets
2. reconstructs metric semantics
3. formulates hypotheses
4. writes and executes SQL
5. runs statistical tests
6. checks confounders
7. asks targeted questions
8. searches documentation
9. creates counterfactual analyses
10. verifies findings
11. produces an auditable research artifact

This is no longer Text-to-SQL. It is an **autonomous empirical scientist operating over organizational data**.

## A research strategy from near-term to moonshot

The best path is not to jump directly to item 20. Build a sequence where every stage is publishable and composes into the next:

1. uncertainty-aware adaptive tool routing
2. information-gain clarification
3. verifier bank + counterexample generation
4. optimizer-in-the-loop reasoning
5. temporal semantic memory
6. SQL Agent Gym with learned policies
7. synthetic organizations + long-horizon adaptation
8. autonomous data researcher

The important thesis is that **Text-to-SQL can become the controlled experimental substrate for general-purpose agents that reason, act, verify, remember, and learn in executable environments.**
