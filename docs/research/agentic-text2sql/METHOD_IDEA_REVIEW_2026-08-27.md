# Method-Focused Text-to-SQL Idea Review — 2026-08-27

**Status:** idea/research-design stage only. No benchmark claims in this document are produced by new experiments on this branch.

**Selection rule:** anchor-paper-first. Each candidate must have: (1) a recent strong anchor paper, (2) a concrete reproducible limitation, (3) an explicit algorithm/system delta, (4) a single primary metric, (5) strong baselines, (6) a 20–50 sample falsification test, and (7) a kill criterion.

The following five ideas survived the current review pass. Generic error analysis, new benchmark-only proposals, generic RAG/agent/judge additions, prompt swaps, backbone swaps, and directions that only rename known mechanisms were excluded.

---

## Rank 1 — Disagreement-Guided SQL Probe Selector

### Anchor Paper

**SDE-SQL: Enhancing Text-to-SQL Generation in Large Language Models via Self-Driven Exploration with SQL Probes** — Wenxuan Xie, Yaxun Dai, Wenhao Jiang, ACL 2026 Main.

- Task: use executable SQL probes to explore database content and improve Text-to-SQL generation.
- Public evaluation: BIRD-style execution-based evaluation; paper reports clear gains over vanilla generation.
- Core method: question/schema-conditioned self-driven probe generation followed by SQL generation/refinement.
- Reproducible limitation: probes are primarily driven by the question/entity state and previous observations. The method does not explicitly condition probe selection on disagreement among multiple plausible SQL candidates.
- Follow-up collision check: active execution is crowded (SDE-SQL, PExA, SQL-Trail-style interaction), so novelty cannot be “use more probes.” The research object here is candidate-disagreement-conditioned diagnostic probing under a fixed DB-call budget.

### Task Definition

**Input:** natural-language question, schema, K SQL candidates, previous DB observations.  
**Intermediate object:** a candidate-by-semantic-atom disagreement matrix over tables, columns, join edges, predicates, literals, aggregation and grouping choices.  
**Output:** the next diagnostic SQL probe, followed by a final selected/generated SQL once the probe budget is exhausted.

### Exact Delta

| Dimension | Anchor | This idea |
|---|---|---|
| Input representation | question + schema + exploration history | question + schema + K SQL candidates + disagreement matrix |
| Intermediate representation | implicit target/condition entities | candidate partitions induced by semantic atoms |
| Training objective | prompt-driven / no explicit selector objective | maximize expected candidate discrimination per probe cost |
| Inference | LLM freely proposes probes | compile legal probes from candidate disagreements, then select by utility |
| Supervision | execution observations | candidate signatures + execution observations; optional learned utility later |
| Evaluation | downstream EX | EX at fixed probe budget |

A training-free first version selects

\[
a^*=\arg\max_a \frac{H(C)-\mathbb{E}_o[H(C\mid o,a)]}{Cost(a)}.
\]

This is not a generic routing module: the action space is restricted to diagnostic SQL probes automatically compiled from the current SQL candidate disagreements.

### Primary Metric

**Execution Accuracy @ 3 Probes (EX@3):** fraction of tasks whose final SQL executes to the correct denotation when at most three diagnostic probes are allowed before the final SQL.

### Secondary Metrics

- mean diagnostic DB calls;
- token cost;
- EX@1/2/5;
- cost-normalized success.

### Core Hypothesis

On BIRD-dev, with the same backbone, candidate pool, and a maximum of three diagnostic probes, disagreement-guided probing improves final EX by at least **3 absolute points** over the official/faithful SDE-style probe policy without increasing mean probe count.

### Strong Baselines

1. SDE-SQL probe policy;
2. PExA-style atomic exploration;
3. random candidate-derived probe;
4. no-probe generation.

### Minimal 20–50 Example Test

Select 40 BIRD-dev tasks where the base model produces at least two distinct executable SQL candidates and Oracle@4 = 1. Freeze the same four candidates for all methods and allow at most two probes.

- Expected observation: disagreement-guided probing resolves candidate uncertainty more often than generic probing.
- Success criterion: at least 4 additional correct tasks out of 40 versus the SDE-style policy with the same probe budget.
- **Kill criterion:** fewer than 2 additional correct tasks, or a large fraction of disagreements cannot be compiled into legal/cheap probes.

### Full Experiment

- Datasets: BIRD plus Spider/another cross-database split.
- Baselines: SDE-SQL, PExA-style probing, random probe, no-probe.
- Budgets: 1/2/3/5 probes.
- Cross-schema: database-held-out evaluation.
- Reporting: database-level bootstrap 95% confidence intervals.

### Ablations

1. remove disagreement conditioning;
2. remove cost normalization;
3. fixed K versus adaptive K.

### Risk / Stop Conditions

Stop if Oracle@K is high but the selector does not improve Top-1 EX, if a simple random/heuristic probe matches the method, or if the EX–DB-call Pareto frontier does not move.

### Final Rating

- Anchor Strength: 5/5
- Quantifiability: 5/5
- Novelty: 4/5
- Feasibility: 5/5
- Reproduction Cost: 4/5
- Incremental-Risk: 4/5

**Two-sentence pitch:** SDE-SQL shows that active database exploration helps, but it does not ask which observation would best distinguish the SQL hypotheses currently under consideration. We compile diagnostic probes from candidate disagreements and select the probe with the largest expected discrimination per DB cost.

---

## Rank 2 — Budgeted Connected Schema Selector

### Anchor Paper

**OpenSQL: Data-Efficient Text-to-SQL for Open-Source LLMs via Synthesized Intermediate Supervision** — Ruilin Hu, Yuyu Luo, Guoliang Li, Shuangqiao Wu, Yun Luo, PVLDB 2026.

- Task: train open-source Text-to-SQL models with synthesized intermediate supervision.
- Core method: global-local schema linking, diverse SQL generation and stepwise selection.
- Data/evaluation: BIRD-style Text-to-SQL evaluation with open-source models.
- Reproducible limitation: schema linking predicts relevant schema elements, but downstream SQL requires a join-connected executable subgraph; high table/column recall can still omit a necessary join path.
- Follow-up collision check: SchemaGraphSQL and bidirectional schema-linking work already use graph/path ideas. Therefore “add graph reasoning” is not sufficient novelty; the delta must be a structured, token-budgeted connected-set prediction objective and must beat simple FK closure baselines.

### Task Definition

**Input:** natural-language question, full schema graph, schema token budget B.  
**Intermediate object:** query-conditioned node and join-edge scores.  
**Output:** a connected table/column subset whose serialization fits within B tokens.

### Exact Delta

| Dimension | Anchor | This idea |
|---|---|---|
| Input representation | serialized schema | typed schema graph |
| Intermediate representation | element relevance | terminal scores + join-edge support scores |
| Training objective | element/schema-link supervision | structured connected-subgraph + join-path loss |
| Inference | global retrieve then local refine | budgeted connected-subgraph decoding |
| Supervision | gold schema elements | gold tables/columns + join edges extracted from gold SQL |
| Evaluation | downstream EX | Join-Path Recall at schema budget |

The decoder approximately solves

\[
S^*=\arg\max_{S\subseteq G}\sum_{v\in S}w_v+\sum_{e\in S}w_e
\]
subject to `Tokens(S) <= B` and `S` being connected.

### Primary Metric

**Join-Path Recall@B:** for gold join-edge set \(E_g\) and edges available in the selected schema \(E_s\),

\[
JPR@B=\frac{|E_g\cap E_s|}{|E_g|}
\]

under a fixed serialized-schema token budget B.

### Secondary Metrics

- Table Recall;
- Column Recall;
- downstream Execution Accuracy;
- schema tokens.

### Core Hypothesis

At a schema budget equal to 25% of the full schema serialization, the structured selector improves Join-Path Recall by at least **8 absolute points** over the OpenSQL linker and improves downstream EX by at least **2 points**.

### Strong Baselines

1. OpenSQL global-local linker;
2. SchemaGraphSQL;
3. bidirectional schema-linking baseline;
4. independent top-K plus shortest-path closure;
5. full schema reference.

### Minimal 20–50 Example Test

Choose 40 BIRD questions requiring at least three tables or at least two join edges. Reuse existing table relevance scores and compare:

- independent top-K;
- shortest-path closure;
- prize-collecting connected closure.

Success requires at least +10 JPR points with less than 20% growth in selected tables.

**Kill criterion:** shortest-path closure matches the structured method, or JPR improves without any downstream EX gain.

### Full Experiment

- Datasets: BIRD + Spider/Spider2-compatible cross-database set.
- Baselines: OpenSQL, SchemaGraphSQL, bidirectional linker, full schema.
- Budgets: 10/25/50% schema tokens.
- Cross-schema: database-held-out testing.
- Reporting: DB-level bootstrap 95% confidence intervals.

### Ablations

1. remove learned edge weights;
2. remove connectivity constraint;
3. remove explicit token-budget objective.

### Risk / Stop Conditions

Stop if a deterministic FK closure heuristic is as good as the learned/structured method, if retrieval metrics improve without EX improvement, or if gains disappear outside multi-table queries.

### Final Rating

- Anchor Strength: 5/5
- Quantifiability: 5/5
- Novelty: 3.5/5
- Feasibility: 5/5
- Reproduction Cost: 4/5
- Incremental-Risk: 3/5

**Two-sentence pitch:** Existing schema linking optimizes whether relevant elements are retrieved, but executable SQL requires those elements to form a complete relational support graph. We directly predict a join-connected schema subset under a token budget and optimize join-path recall rather than independent element recall.

---

## Rank 3 — Correlation-Aware SQL Candidate Ranker

### Anchor Paper

**DeepEye-SQL: A Software-Engineering-Inspired Text-to-SQL Framework** — Boyan Li, Chong Chen, Zhujun Xue, Yinan Mei, Yuyu Luo, SIGMOD 2026.

- Task: improve Text-to-SQL reliability through N-version candidate generation, deterministic testing and confidence-aware selection.
- Public artifacts: repository/runbooks for major Text-to-SQL benchmarks.
- Core limitation: execution-result clusters and repeated candidate agreement can overstate confidence because candidates generated through similar reasoning pathways are not independent.
- Follow-up collision check: DPC already attacks systematic errors through cross-paradigm candidate validation, so any new selector must be evaluated directly against DPC rather than only majority voting or self-consistency.

### Task Definition

**Input:** K SQL candidates, normalized ASTs, execution results and generation lineage/provenance.  
**Intermediate object:** candidate error-correlation matrix and correlation-adjusted effective vote.  
**Output:** calibrated correctness score per candidate and final Top-1 SQL.

### Exact Delta

| Dimension | Anchor | This idea |
|---|---|---|
| Input representation | candidates + execution results | candidates + execution + AST + generator lineage |
| Intermediate representation | result clusters | correlation-adjusted effective evidence |
| Training objective | confidence heuristic | candidate correctness log-loss / pairwise ranking |
| Inference | cluster majority + adjudication | correlation-discounted posterior ranking |
| Supervision | result agreement | EX labels + historical joint-error statistics |
| Evaluation | EX | Candidate Selection Top-1 EX |

A simple first model uses effective sample size:

\[
N_{eff}=\frac{(\sum_iw_i)^2}{\sum_iw_i^2+2\sum_{i<j}w_iw_j\rho_{ij}}.
\]

### Primary Metric

**Candidate Selection Top-1 EX:** fraction of tasks where the candidate ranked first by the selector executes to the correct denotation, with the candidate pool held fixed.

### Secondary Metrics

- Candidate MRR;
- Expected Calibration Error;
- Oracle EX@K;
- selector token cost.

### Core Hypothesis

With DeepEye candidate generation held fixed, correlation-aware ranking improves Top-1 EX by at least **2 absolute points** over DeepEye's confidence selector while adding no candidate-generation cost.

### Strong Baselines

1. DeepEye confidence selector;
2. DPC;
3. self-consistency/majority voting;
4. random selector;
5. pairwise LLM judge.

### Minimal 20–50 Example Test

Use 50 released/fixed candidate pools where Oracle@K = 1 but the original selector is wrong. Apply a training-free discount based on same generator lineage plus high normalized-AST similarity.

- Success: repair at least 5 of 50 cases while causing at most 2 regressions.
- **Kill criterion:** DPC or a simple diversity heuristic already captures the same gain, or wrong candidates do not exhibit measurable correlation structure.

### Full Experiment

- Datasets: BIRD + Spider.
- Candidate sources: DeepEye pool plus a second generation family.
- Baselines: DeepEye selector, DPC, self-consistency, pairwise judge.
- Cross-generator test: train/fit correlation model on one candidate family, test on another.
- Reporting: database-level bootstrap confidence intervals.

### Ablations

1. AST similarity only;
2. generator lineage only;
3. no correlation correction.

### Risk / Stop Conditions

Stop if calibration improves without Top-1 EX, if DPC dominates at acceptable cost, or if the method requires regenerating a different candidate pool to show gains.

### Final Rating

- Anchor Strength: 5/5
- Quantifiability: 5/5
- Novelty: 3.5/5
- Feasibility: 5/5
- Reproduction Cost: 5/5
- Incremental-Risk: 3/5

**Two-sentence pitch:** N-version SQL candidates are correlated samples, so raw consensus can turn common-mode errors into false confidence. We estimate candidate correlation from AST and generation lineage and discount redundant evidence before ranking candidates.

---

## Rank 4 — Write-Sensitivity Clarification Gate

### Anchor Paper

**BIRD-INTERACT: Re-imagining Text-to-SQL Evaluation via Lens of Dynamic Interactions** — Nan Huo et al., ICLR 2026 Oral.

- Task: interactive database-agent evaluation with hierarchical knowledge, user clarification, tool actions and CRUD.
- Public artifacts: benchmark repository/environment and interaction protocols.
- Reproducible limitation: current policies choose whether to ask based on generic uncertainty/interaction reasoning, but the same ambiguity has very different consequences for SELECT versus INSERT/UPDATE/DELETE.
- Follow-up collision check: generic clarification routing is crowded. The proposed research object is specifically counterfactual **write-set sensitivity**, not model confidence.

### Task Definition

**Input:** dialogue state, unresolved semantic alternatives, candidate INSERT/UPDATE/DELETE SQL.  
**Intermediate object:** affected-row sets under alternative plausible interpretations.  
**Output:** `ASK(question)` or `EXECUTE(sql)`.

### Exact Delta

| Dimension | Anchor | This idea |
|---|---|---|
| Input representation | dialogue + tool context | dialogue + candidate write + ambiguity alternatives |
| Intermediate representation | implicit model uncertainty | counterfactual write-set difference |
| Training objective | none/generic action choice | minimize failed writes under interaction budget |
| Inference | model directly chooses next action | deterministic or learned clarification gate before writes |
| Supervision | user/tool feedback | task tests + affected-row sensitivity |
| Evaluation | task reward | CRUD success at fixed interaction budget |

For two plausible resolutions \(z_1,z_2\), let affected rows be \(W_1,W_2\). Define

\[
S_w=\frac{|W_1\triangle W_2|}{|W_1\cup W_2|+\epsilon}.
\]

Ask before commit when \(S_w>\tau\).

### Primary Metric

**CRUD Task Success @ Fixed BIRD-Coin Budget:** fraction of CRUD tasks whose final evaluator tests all pass under the same starting interaction budget.

### Secondary Metrics

- user turns;
- BIRD coins/tool cost;
- premature-write rate;
- latency.

### Core Hypothesis

On the BIRD-INTERACT CRUD subset, with the same model and coin budget, the write-sensitivity gate improves task success by at least **4 absolute points** while adding at most **0.5 clarification turns per task**.

### Strong Baselines

1. official/faithful a-Interact policy;
2. model uncertainty threshold;
3. always ask before write;
4. never ask;
5. explicit caution prompt.

### Minimal 20–50 Example Test

Select 30 INSERT/UPDATE/DELETE tasks with a documented critical ambiguity. Use an inference-time gate only.

- Success: prevent at least four wrong writes with ten or fewer extra clarifications across 30 tasks.
- **Kill criterion:** ambiguity alternatives usually produce identical write sets, or always-ask dominates at the same budget.

### Full Experiment

- Datasets: Mini/Full BIRD-INTERACT and matched SELECT controls.
- Baselines: official policy, uncertainty threshold, always-ask, never-ask.
- Models: at least two backbones.
- Reporting: paired bootstrap confidence intervals.

### Ablations

1. answer uncertainty instead of write-set sensitivity;
2. no counterfactual row estimation;
3. calibrated versus fixed threshold.

### Risk / Stop Conditions

Stop if generic uncertainty matches write-set sensitivity, if all gains are explained by asking before every write, or if the counterfactual DB cost eliminates the success benefit.

### Final Rating

- Anchor Strength: 5/5
- Quantifiability: 5/5
- Novelty: 4/5
- Feasibility: 4/5
- Reproduction Cost: 3/5
- Incremental-Risk: 4/5

**Two-sentence pitch:** Interactive SQL agents currently treat ambiguity largely as a confidence problem, but for write operations the relevant quantity is how much the database state changes under competing interpretations. We estimate counterfactual affected-row divergence and only interrupt the user when unresolved semantics materially change the write set.

---

## Rank 5 — Coverage-Budgeted Atomic Test Planner

### Anchor Paper

**PExA: Parallel Exploration Agent for Complex Text-to-SQL** — Tanmay Parekh, Ella Hofmann-Coyle, Shuyi Wang, Sachith Sri Ram Kothur, Srivas Prasad, Yunmo Chen, ACL 2026.

- Task: decompose complex Text-to-SQL tasks into atomic SQL tests, execute them in parallel and synthesize a final query.
- Core limitation: atomic exploration can require many DB calls; tests overlap in semantic coverage, but PExA does not explicitly optimize which subset should be executed under a hard budget.
- Follow-up collision check: generic interaction-budget allocation is crowded, so this idea is specifically about **PExA atomic-test semantic coverage** and must beat random/top-B pruning.

### Task Definition

**Input:** question, schema, M generated atomic SQL tests, DB-call or latency budget B.  
**Intermediate object:** test-by-semantic-atom coverage matrix plus estimated execution cost.  
**Output:** a subset of at most B tests to execute, followed by the final SQL.

### Exact Delta

| Dimension | Anchor | This idea |
|---|---|---|
| Input representation | atomic SQL tests | atomic tests + explicit coverage sets + costs |
| Intermediate representation | implicit semantic coverage | weighted coverage/redundancy matrix |
| Training objective | none | maximize useful coverage under cost |
| Inference | execute broad/full parallel test set | budgeted submodular/set-cover selection |
| Supervision | execution observations | semantic-atom coverage + optional historical utility |
| Evaluation | EX | cost-normalized success |

A training-free first version solves approximately

\[
A^*=\arg\max_{A:Cost(A)\le B}\left|\bigcup_{a\in A}Coverage(a)\right|-\lambda Redundancy(A).
\]

Coverage atoms include target, join, filter, aggregation, grouping, ordering and temporal conditions.

### Primary Metric

**Cost-Normalized Success (CNS):**

\[
CNS=\frac{\#successful\ tasks}{\sum_i DBCalls_i}.
\]

### Secondary Metrics

- Execution Accuracy;
- mean DB calls;
- latency;
- semantic coverage.

### Core Hypothesis

On Spider 2.0/PExA-compatible tasks, executing at most 50% of the original atomic tests reduces EX by no more than 1 point while improving CNS by at least **50%**.

### Strong Baselines

1. original PExA all-tests;
2. random 50% test subset;
3. LLM top-B importance;
4. sequential SDE-style exploration.

### Minimal 20–50 Example Test

Select 20–30 tasks that PExA solves and for which at least six atomic tests are generated. Compare all-tests versus greedy coverage selection at 50% budget.

- Success: retain at least 90% of PExA's solved tasks while reducing DB calls by at least 40%.
- **Kill criterion:** random pruning performs equally well, or the test suite has little redundancy and EX drops sharply.

### Full Experiment

- Datasets: Spider 2.0 plus a BIRD complex-query subset.
- Baselines: PExA, random/top-B pruning, SDE-style sequential probing.
- Budgets: 25/50/75/100% of the original test count.
- Models: at least two backbones if reconstruction permits.
- Reporting: bootstrap confidence intervals over tasks/databases.

### Ablations

1. remove redundancy penalty;
2. LLM importance only;
3. uniform versus measured test cost.

### Risk / Stop Conditions

Stop if random pruning matches the structured planner, if CNS improvement comes only from a large EX drop, or if gains occur only in a tiny high-test-count tail.

### Final Rating

- Anchor Strength: 4/5
- Quantifiability: 5/5
- Novelty: 4/5
- Feasibility: 3.5/5
- Reproduction Cost: 3/5
- Incremental-Risk: 4/5

**Two-sentence pitch:** PExA shows that atomic SQL tests improve complex Text-to-SQL, but it spends database calls on tests with overlapping semantic coverage. We select a cost-bounded subset of atomic tests that maximizes complementary coverage and directly optimize the accuracy–DB-call frontier.

---

# Portfolio Recommendation

### First-line kill tests

1. **Disagreement-Guided SQL Probe Selector** — strongest combination of clean delta, strong anchor and fixed-budget evaluation.
2. **Correlation-Aware SQL Candidate Ranker** — cheapest to falsify because candidate pools can be frozen offline.
3. **Budgeted Connected Schema Selector** — promising but must immediately test whether simple FK/path closure already solves the problem.

### Second-line candidates

4. **Write-Sensitivity Clarification Gate** — strong problem definition but higher environment cost.
5. **Coverage-Budgeted Atomic Test Planner** — quantifiable, but reproduction depends on faithfully reconstructing PExA atomic-test generation.

### Global stop rule

No candidate should proceed to full implementation if its 20–50 sample kill test fails. In particular, do not add extra agents, memory, verifiers, training stages or prompt scaffolding to rescue a weak core hypothesis.
