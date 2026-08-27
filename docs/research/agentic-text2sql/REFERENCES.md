# Annotated References: Agentic Text-to-SQL

This reading list emphasizes work that changes the problem from single-shot SQL generation toward retrieval, decomposition, interaction, verification, debugging, and adaptive agent behavior.

## Benchmarks

### Spider 2.0 — Real-World Enterprise Text-to-SQL Workflows

- Repository: https://github.com/xlang-ai/Spider2
- Paper: https://arxiv.org/abs/2411.07763

Why it matters: Spider 2.0 substantially increases realism over classic Spider, with enterprise databases, large schemas, multiple SQL dialects, and code-agent workflows. It is a useful stress test for long-horizon schema discovery and data-engineering behavior rather than only semantic parsing.

### BIRD

- Website: https://bird-bench.github.io/
- Repository: https://github.com/AlibabaResearch/DAMO-ConvAI/tree/main/bird

Why it matters: BIRD introduced large databases, external knowledge, value grounding, and an efficiency-aware setting. It became one of the main post-Spider testbeds for LLM-era Text-to-SQL.

### LiveSQLBench

- Repository: https://github.com/bird-bench/livesqlbench

Why it matters: Designed as a live, contamination-resistant benchmark family. Recent releases include industrial-scale schemas, hierarchical knowledge, CRUD-oriented tasks, Agent mode, and business-rule drift. These properties make it particularly relevant to persistent and adaptive data agents.

### BIRD-INTERACT

- Website: https://bird-interact.github.io/
- Repository: https://github.com/bird-bench/BIRD-Interact
- ICLR 2026 paper: https://openreview.net/forum?id=nHrYBGujps

Why it matters: Explicitly reframes Text-to-SQL as dynamic interaction. It provides conversational and active agentic modes with a user simulator, database environment, hierarchical knowledge, and executable test cases across BI and CRUD tasks.

## Decomposition and context selection

### DIN-SQL — Decomposed In-Context Learning of Text-to-SQL

- Paper: https://arxiv.org/abs/2304.11015

Key idea: break Text-to-SQL into schema linking, query classification/decomposition, generation, and self-correction. DIN-SQL is an important bridge between single-shot prompting and structured reasoning pipelines.

### MAC-SQL — Multi-Agent Collaborative Text-to-SQL

- Paper: https://arxiv.org/abs/2312.11242
- Repository: https://github.com/wbbeyourself/MAC-SQL

Key idea: a decomposer works with selector and refiner agents. This is an early influential example of using agent collaboration and tool-like context reduction for large databases.

### CHESS — Contextual Harnessing for Efficient SQL Synthesis

- Paper: https://arxiv.org/abs/2405.16755

Key idea: emphasizes database entity retrieval, schema selection, generation, and revision to cope with large and noisy database contexts. Particularly relevant to the observation that context engineering is a first-class Text-to-SQL problem.

## Candidate diversity and test-time compute

### CHASE-SQL

- Paper: https://arxiv.org/abs/2410.01943

Key idea: generate diverse SQL candidates using different reasoning paths and select among them with pairwise/tournament-style evaluation. This motivates research on adaptive rather than fixed test-time compute allocation.

### XiYan-SQL

- Paper: https://arxiv.org/abs/2411.08599

Key idea: a multi-generator ensemble and selection framework, demonstrating the strength of specialized generation and candidate selection for Text-to-SQL.

### Agentar-Scale-SQL

- Paper: https://arxiv.org/abs/2509.24403

Why it matters: represents the scaling direction in which multiple trajectories/candidates and stronger test-time search improve SQL performance. The open question is how to allocate this compute selectively by difficulty and uncertainty.

## Verification and software-engineering framing

### DeepEye-SQL — Software-Engineering-Inspired Text-to-SQL

- Paper: https://arxiv.org/abs/2510.17586

Key idea: treats SQL synthesis as a small software-development process with grounding, N-version generation, deterministic verification, targeted revision, and confidence-aware selection. This is one of the clearest signals that reliability requires orchestration, not only a stronger decoder.

### SWE-SQL / BIRD-CRITIC

- Search entry point: https://github.com/bird-bench

Why it matters: extends the research surface from writing SQL to diagnosing and repairing SQL/database failures. This is strategically important because a general data agent should generate, debug, optimize, and operate—not only translate questions.

## Agentic approaches

### ReFoRCE

- Paper: https://arxiv.org/search/?query=ReFoRCE+text-to-SQL&searchtype=all

Why it matters: part of the recent move toward iterative exploration and refinement on difficult enterprise-style Text-to-SQL tasks. The broader lesson is that long-horizon interaction is increasingly competitive with fixed pipelines.

### LiveSQLBench-Agent

- Repository: https://github.com/bird-bench/livesqlbench

Why it matters: provides an explicit agent scaffold with isolated database environments and multi-provider model support, making it a practical platform for controlled orchestration experiments.

### BIRD-Interact-ADK

- Repository: https://github.com/bird-bench/BIRD-Interact

Why it matters: modularizes agent, user simulator, and DB environment into separate services. This is useful infrastructure for learned interaction policies, user-question research, and reproducible agent traces.

## Additional concepts worth importing from adjacent fields

### Counterexample-Guided Inductive Synthesis (CEGIS)

Text-to-SQL candidate verification can borrow the CEGIS pattern: synthesize a candidate, search for a counterexample, refine, and repeat. Database execution makes counterexample-based verification unusually practical compared with free-form language tasks.

### Property-based testing

Frameworks such as QuickCheck/Hypothesis inspire a verifier that generates structured test cases and invariants rather than relying exclusively on LLM critique.

### Query optimization

Database optimizers expose cost, cardinality, join order, scans, and selectivity. These signals are currently underused as feedback for Text-to-SQL agents and could form a systems-oriented research contribution.

### Active learning / value of information

Clarification and schema exploration can be modeled using expected information gain: choose the observation whose expected reduction in decision uncertainty is largest relative to interaction cost.

### Contextual bandits / offline RL

Tool routing can be treated as a cost-sensitive policy-learning problem. Logged SQL-agent traces provide a plausible path toward offline training without risky online interaction with production databases.

## Suggested reading order

1. Spider 2.0 — understand why enterprise Text-to-SQL is still hard.
2. BIRD and LiveSQLBench — understand modern context and evaluation requirements.
3. DIN-SQL — decomposition baseline.
4. MAC-SQL and CHESS — context selection and multi-component orchestration.
5. CHASE-SQL / XiYan-SQL — candidate diversity and selection.
6. DeepEye-SQL — verification-oriented software engineering framing.
7. BIRD-INTERACT — interactive/agentic evaluation.
8. Then study active learning, property-based testing, optimizer feedback, and offline RL as sources of ideas not yet fully exploited in Text-to-SQL.

## Research takeaway

The literature trajectory is consistent: performance improvements increasingly come from **what the system does around the model**—retrieval, decomposition, execution, verification, selection, repair, interaction, and memory. The next step is to make that orchestration itself adaptive, measurable, and learnable.
