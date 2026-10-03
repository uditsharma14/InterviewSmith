# Resume-Project-Preparation

Interview and resume prep for Udit Sharma, centered on the AI-assisted incident/provisioning intelligence project and the surrounding resume highlights.

## Start here

- **[`Interview Stories.md`](Interview%20Stories.md)**: **practice from this first.** It has answer-first, 60–90 second spoken versions of every main story (intro, NCC, Instant Fund, LCM, AI platform, disagreement, mistake, leadership), each with a one-line takeaway and short follow-up answers. It was written in response to interview feedback asking for concise, audience-focused storytelling. The long versions in other files are follow-up material.
- **[`Interview_Prep_Top3.md`](Interview_Prep_Top3.md)**: the main prep doc. It has likely interviewer questions and draft answers for the top 3 resume highlights: the AI incident intelligence platform, Capital One Instant Fund / Apple Wallet, and Discover modernization. It also has a business-impact/metrics section, productionization challenges, and a domain glossary. It embeds the architecture diagram below.
- **[`token-provisioning-architecture-highlevel.svg`](token-provisioning-architecture-highlevel.svg)**: high-level architecture diagram for the AI platform. It shows the path from a device provisioning/token-enablement failure through ingestion, RAG/orchestration, the human-review gate and remediation, closing the loop.
- **[Token Provisioning Intelligence (detailed architecture, hosted)](https://claude.ai/code/artifact/9fe6101b-b8ca-4879-a615-f245e694e762)**: the fuller version of the same diagram, with a component-by-component breakdown and a trade-offs FAQ. Useful as a leave-behind link or for review before a whiteboard round.

- **[`interview Stories_2.md`](interview%20Stories_2.md)**: companion to `Interview Stories.md`. Four stories with the clearest hands-on implementation detail: the NCC dual-write and 5% rollback, the Instant Fund bulk update job, the LCM Kafka event handlers, and the AI platform guardrails. Each comes with a note on claiming only what you personally built.
- [`Mock-interview.md`](Mock-interview.md): questions from a resume mock interview, grouped by topic, with the answers given. One example: the Discover JSP-to-React migration via the strangler fig pattern. Use it to re-drill follow-ups.

## Resume

- [`Resume Based.md`](Resume%20Based.md): resume-based introduction, expected follow-ups, staff-level leadership questions, Apple Wallet provisioning deep-dive, and Instant Fund (10M tokens) architecture.
- The resume source (`Udit_Sharma_Resume_v7.tex`) and compiled PDF (`Udit_Sharma_Resume_30_08.pdf`) were removed from this repo in commit `e368c89`. Recover them with `git show e368c89^:Udit_Sharma_Resume_v7.tex`.

## AI platform

- **[`AI_Incident_Intelligence_Platform.md`](AI_Incident_Intelligence_Platform.md)**: the single design doc for the AI platform.
  - **Part I** covers the problem statement, data sources, the current (manual) process, the proposed process, architecture, RAG pipeline, tools vs. RAG, agent responsibilities, guardrails, HITL, the knowledge feedback loop, two worked examples (OTP failure, Apple schema change), business value, observability, security, why LangGraph, prototype status, and the interview pitch.
  - **Part II** holds the supporting notes:
    - A. data source inventory
    - B. step-by-step RAG build
    - C. multi-agent workflow design
    - D. enterprise architecture view (Mermaid diagram, build phases, follow-up questions, engineering challenges)
    - E. full business-impact/metrics draft
    - F. production challenges: spoken answer, multi-agent challenges, session notes
- **[`AWS_Architecture_Payment_Reliability.md`](AWS_Architecture_Payment_Reliability.md)**: the platform on AWS. It covers the stack by layer (Bedrock, Step Functions, LangGraph on Fargate, Knowledge Bases + OpenSearch, Lambda tools, Athena), the end-to-end flow with a Mermaid diagram, design decisions, PCI security, cost controls, the interview pitch and follow-up questions.
- **[`RAG_Pipeline_Architecture.md`](RAG_Pipeline_Architecture.md)**: detailed RAG design. It covers offline indexing (ingestion, PII/PAN redaction, document-aware and parent–child chunking, metadata, hybrid index), online retrieval (query understanding, hybrid search + RRF, re-ranking, context assembly, cited structured output, grounding checks), the feedback loop, evaluation, the AWS mapping, the interview pitch and 23 follow-up questions with answers.
- [`LangChain.md`](LangChain.md): LangChain building blocks (prompts, models, parsers, memory, chains, embeddings, agents, eval, LCEL, routing), with examples from the incident platform.
- [`LangGraph.md`](LangGraph.md): LangGraph overview and interview questions.
- [`Intelligent-agent/Agents.py`](Intelligent-agent/Agents.py): prototype agent code.
- `ChatGPT Image Aug 30, 2026, 10_42_17 AM.png`: early concept image, kept for reference only.

## Interview question banks

- [`AI_Interview_Questions.md`](AI_Interview_Questions.md) covers:
  - AI/ML system-design questions
  - backend/API scenario questions (latency, idempotency, retries, auth)
  - advanced RAG questions (multi-hop, hybrid, agentic, query understanding)
  - patterns behind AI interview questions
  - a focused 40-question set (LLMs, agents, LangGraph, MCP, RAG)
  - sample answers on chunking, embeddings and Qdrant
- [`Tech-Behavioural.md`](Tech-Behavioural.md): leadership/architecture and system/technical STAR stories.

## SQL & data modeling

- **[`SQL_Interview_Guide.md`](SQL_Interview_Guide.md)**: prep for the LexisNexis role. It covers 15 must-know concepts (normalization, 3NF, star/snowflake, fact/dimension, SCD, joins, indexing, composite indexes, optimization, execution plans, ACID, isolation, locking, partitioning/sharding, SQL vs NoSQL), each with a 20-second answer, details, SQL examples and follow-ups. It also has 8 practice problems plus bonus problems with solutions, data-modeling walkthroughs (legal research, identity/risk, analytics star schema) and a one-page cheat sheet.
- **[`SQL_Advanced_Practice.md`](SQL_Advanced_Practice.md)**: the second SQL guide, a query-writing workout. It has a copy-paste seed dataset, then:
  - 10 rapid-fire classics with the edge cases fixed (ties, NULLs, the default window frame, MySQL error 1093)
  - 14 advanced patterns: self-join, recursive org chart, pivot, percent of total, median/p90, date spine, sessionization, gaps-and-islands streaks, retention, relational division, mode with ties, overlapping intervals plus exclusion constraint, the `LAST_VALUE` frame trap, and idempotent upsert for out-of-order events
  - a SQL-traps table, a Postgres/MySQL/SQL Server dialect table, and a "question wording → pattern" picker

  Every query was run on PostgreSQL 16, and the outputs shown are real. The MySQL claims were checked on MySQL 9.3.
- **[`SQL_Oracle_Window_Functions.md`](SQL_Oracle_Window_Functions.md)**: Oracle analytic functions on an `orders` table.
  - **Core functions:** MIN/MAX/AVG/COUNT `OVER`, running totals (the default-frame tie trap), LAG/LEAD with % change and days between orders, ROW_NUMBER/RANK/DENSE_RANK, filtering on a window result, moving average, NTILE.
  - **Oracle-only features:** the `ROWNUM` trap vs. `FETCH FIRST`, `KEEP (DENSE_RANK LAST)`, `RATIO_TO_REPORT`, `LISTAGG`, `IGNORE NULLS`, plus Oracle gotchas (`''` is NULL, `DATE` has a time part, `MERGE`).
  - **How it was checked:** the standard-SQL sections ran on PostgreSQL 16. The Oracle-only outputs are expected values, computed with Postgres equivalents, and were not run on Oracle.
- [`Lexis_Nexis_interview.md`](Lexis_Nexis_interview.md): Q&A for the LexisNexis data-engineering round. It covers a hybrid OLTP/OLAP model, star vs. snowflake, OLTP-to-warehouse ETL, managed services vs. staff augmentation, TDD and testing layers, diagnosing slow queries (statistics, cardinality), and Agile vs. Waterfall.

- **[`Elastic-Search.md`](Elastic-Search.md)**: 10 Lead/Senior Elasticsearch questions with answers. Topics: cluster sizing, shards, keeping it in sync with Postgres (CDC/outbox/Kafka), slow-query troubleshooting, mappings and analyzers, high availability and disaster recovery, zero-downtime reindexing, external versioning against duplicate or out-of-order events, choosing between search and database engines, and deep pagination. Each has a 30-second answer, details and examples, and there's a cheat sheet at the end.

## Deployment & infrastructure

- [`Project_Deployment_infra.md`](Project_Deployment_infra.md): infra and application architecture with answer-first follow-ups. Topics: Helm and CI/CD build-vs-deploy separation, replica count and HPA sizing, per-environment config through Helm, Helm vs. Spring profiles, end-to-end traffic flow, active-standby regional failover and data replication. Items marked `[fill in]` need real numbers.

## Payments domain prep

- [`Payments_Modernization.md`](Payments_Modernization.md) opens with three Staff-level STAR stories, strongest first: NCC (provisioning eligibility and legacy coexistence), Instant Fund (10M-token backfill) and LCM (token lifecycle events). Behind them is supporting material: the project overview, NCC and LCM API deep-dives with follow-up questions, DMS migration challenges, failure/retry/trade-off questions with draft answers, Staff-level upgrades, and a map from each [`Tech-Behavioural.md`](Tech-Behavioural.md) question to the right story. Items marked **[confirm]** need real facts before use.
- [`Payment_Domain.md`](Payment_Domain.md): reference glossary for the digital payments / Apple Wallet / tokenization ecosystem, covering PAN vs. DPAN, BIN, Apple Pay participants, provisioning/lifecycle terms, ISO 8583, HSMs, and authorization vs. settlement.

## Career & study prep

- [`Career_Prep.md`](Career_Prep.md): what AI Forward Deployed Engineer interviews look for, a study roadmap with resources, and a 15-concept AI-engineering reading list.

## Note on tooling references

Some design notes mention Kibana/ELK for log search, while the interview prep doc and architecture diagram use Splunk, per the actual stack. Check which one is accurate for your environment before an interview.
