# Tasks: Multi-Agent Collaborative Investment Analysis

**Input**: Design documents from `/specs/002-multi-agent-data/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **packages/core/**: Shared schemas (JSON Schema, TypeScript)
- **packages/mcp-server/**: Python FastMCP server
- **packages/extension/**: Chrome Extension (MV3, TypeScript)

---

## Phase 1: Setup

**Purpose**: Add new dependencies and create directory structure for collaborative agents

- [x] T001 Add duckduckgo-search dependency to packages/mcp-server/pyproject.toml
- [x] T002 Create collaborative agents directory at packages/mcp-server/src/agents/collaborative/
- [x] T003 Create collaborative agents __init__.py at packages/mcp-server/src/agents/collaborative/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Models, schemas, provider support, and base classes that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Pydantic Models (packages/mcp-server)

- [x] T004 [P] Create collaborative entity models (NewsItem, FundamentalsSnapshot, FinancialMetric, CrossReferenceAnalysis, Divergence, MacroContext) and agent output models (NewsAgentOutput, FundamentalsAgentOutput, RiskAgentOutput, MacroAgentOutput, SynthesisAgentOutput — each with confidence_score field) in packages/mcp-server/src/models/collaborative.py
- [x] T005 [P] Create AgentMessage, CommunicationLog, and AgentConfig Pydantic models in packages/mcp-server/src/models/collaborative.py
- [x] T006 Add NRP value to Provider enum in packages/mcp-server/src/models/idea_report.py
- [x] T007 Add optional enrichment fields (news_context, fundamentals_summary, cross_reference_analysis, macro_context, agent_attributions, communication_log) to IdeaReport in packages/mcp-server/src/models/idea_report.py
- [x] T008 Add agent_configs field to UserSettings in packages/mcp-server/src/models/idea_report.py

### Provider & Tool Calling (packages/mcp-server)

- [x] T009 Add NRP.ai provider routing (openai/ prefix + real api_key + base_url) to packages/mcp-server/src/providers/llm.py
- [x] T010 Add tool calling support to LLMProvider.complete() with tools parameter, tool call loop, and tool result handling in packages/mcp-server/src/providers/llm.py
- [x] T011 Implement web search tool functions (web_search and news_search using duckduckgo-search) in packages/mcp-server/src/tools/web_search.py

### Collaborative Agent Base (packages/mcp-server)

- [x] T012 Implement CollaborativeAgent base class with tool calling support, send_message/receive_messages, and agent_id in packages/mcp-server/src/agents/collaborative/base.py
- [x] T013 Implement Coordinator class with parallel agent execution, message bus, and round enforcement (max 3) in packages/mcp-server/src/agents/collaborative/coordinator.py

### Shared Schemas (packages/core)

- [x] T014 [P] Define NewsItem JSON Schema in packages/core/src/schemas/news-item.json
- [x] T015 [P] Define FundamentalsSnapshot and FinancialMetric JSON Schema in packages/core/src/schemas/fundamentals-snapshot.json
- [x] T016 [P] Define CrossReferenceAnalysis and Divergence JSON Schema in packages/core/src/schemas/cross-reference.json
- [x] T017 [P] Define MacroContext JSON Schema in packages/core/src/schemas/macro-context.json
- [x] T018 [P] Define AgentMessage JSON Schema in packages/core/src/schemas/agent-message.json
- [x] T019 [P] Define CommunicationLog JSON Schema in packages/core/src/schemas/communication-log.json
- [x] T020 [P] Define AgentConfig JSON Schema in packages/core/src/schemas/agent-config.json
- [x] T021 Extend idea-report.json with optional enrichment fields in packages/core/src/schemas/idea-report.json

### Extension Types (packages/extension)

- [x] T022 Generate TypeScript types for enrichment entities (NewsItem, FundamentalsSnapshot, CrossReferenceAnalysis, MacroContext, AgentMessage, CommunicationLog, AgentConfig) in packages/extension/src/types/enriched.ts
- [x] T023 Add NRP to provider enum and agent_configs to UserSettings type in packages/extension/src/types/

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Data-Enriched Investment Idea (Priority: P1) 🎯 MVP

**Goal**: User selects text, receives enriched report with news context and financial fundamentals alongside the text-based thesis

**Independent Test**: Select text mentioning a public company, trigger analysis, verify report contains News Context section with news items and Fundamentals section with financial metrics

### Agent Implementations (packages/mcp-server)

- [x] T024 [P] [US1] Implement News Agent with web_search/news_search tool calling, sentiment extraction, and NewsAgentOutput in packages/mcp-server/src/agents/collaborative/news.py
- [x] T025 [P] [US1] Implement Fundamentals Agent with web_search tool calling, financial metric retrieval, and FundamentalsAgentOutput in packages/mcp-server/src/agents/collaborative/fundamentals.py
- [x] T026 [US1] Implement Synthesis Agent that combines text pipeline output + agent findings into enriched IdeaReport fields in packages/mcp-server/src/agents/collaborative/synthesis.py

### Pipeline Integration (packages/mcp-server)

- [x] T027 [US1] Extend Pipeline.run() to invoke Coordinator after text pipeline completes, passing tickers/entities to collaborative agents in packages/mcp-server/src/agents/pipeline.py
- [x] T028 [US1] Extend FormatterAgent to merge enrichment data (news_context, fundamentals_summary) into IdeaReport in packages/mcp-server/src/agents/formatter.py
- [x] T029 [US1] Handle graceful degradation in pipeline when no tickers found or agents fail (return text-only report) in packages/mcp-server/src/agents/pipeline.py

### Extension UI (packages/extension)

- [x] T030 [US1] Display News Context section in side panel (headlines, sentiment badges, relevance scores, data source indicators) in packages/extension/src/sidepanel/panel.ts
- [x] T031 [US1] Display Fundamentals Summary section in side panel (ticker, metrics table, data source indicator) in packages/extension/src/sidepanel/panel.ts
- [x] T032 [US1] Show active agent progress indicators during enriched analysis in packages/extension/src/popup/popup.ts
- [x] T033 [US1] Pass agent_configs from settings in generate request in packages/extension/src/background/service-worker.ts

**Checkpoint**: User Story 1 complete — enriched reports with news and fundamentals data

---

## Phase 4: User Story 2 - Agent Transparency and Attribution (Priority: P2)

**Goal**: Each report section shows which agent contributed it, and users can view the inter-agent communication log

**Independent Test**: Generate an enriched report, verify each enrichment section displays its source agent label, and the communication log is viewable

### Attribution (packages/mcp-server)

- [x] T034 [US2] Add agent_attributions dict to SynthesisAgent output mapping each report section to contributing agent IDs in packages/mcp-server/src/agents/collaborative/synthesis.py
- [x] T035 [US2] Include communication_log (CommunicationLog from Coordinator) in final IdeaReport in packages/mcp-server/src/agents/pipeline.py

### Extension UI (packages/extension)

- [x] T036 [US2] Display agent attribution labels (e.g., "News Agent", "Fundamentals Agent") on each enrichment section in packages/extension/src/sidepanel/panel.ts
- [x] T037 [US2] Implement communication log viewer showing agent messages with timestamps, sender, recipient, and content in packages/extension/src/sidepanel/panel.ts
- [x] T038 [US2] Add "Agent Log" toggle button to enriched report view in packages/extension/src/sidepanel/panel.ts
- [x] T039 [US2] Show data source badges ("web search" / "LLM knowledge") on news items and fundamentals in packages/extension/src/sidepanel/panel.ts

**Checkpoint**: User Story 2 complete — agent transparency and attribution visible

---

## Phase 5: User Story 3 - Inter-Agent Communication and Cross-Referencing (Priority: P3)

**Goal**: Agents exchange findings across multiple rounds, cross-reference news vs. fundamentals, deduplicate risks, and surface contradictions

**Independent Test**: Analyze text about a company with positive news but declining revenue, verify report flags the divergence and communication log shows agent exchanges

### Risk Agent (packages/mcp-server)

- [x] T040 [US3] Implement Risk Agent that receives findings from News and Fundamentals agents, identifies risks with source attribution, and produces RiskAgentOutput in packages/mcp-server/src/agents/collaborative/risk.py

### Multi-Round Communication (packages/mcp-server)

- [x] T041 [US3] Extend Coordinator to distribute findings between agents after round 1 and run additional communication rounds (up to 3) in packages/mcp-server/src/agents/collaborative/coordinator.py
- [x] T042 [US3] Implement message filtering in Coordinator so agents receive only messages addressed to them or broadcast in packages/mcp-server/src/agents/collaborative/coordinator.py
- [x] T043 [US3] Add round context to CollaborativeAgent.run() so agents can reference other agents' findings in their prompts in packages/mcp-server/src/agents/collaborative/base.py

### Cross-Reference Analysis (packages/mcp-server)

- [x] T044 [US3] Extend Synthesis Agent to produce CrossReferenceAnalysis (convergences, divergences, deduplicated risks) from multi-agent findings in packages/mcp-server/src/agents/collaborative/synthesis.py
- [x] T045 [US3] Extend FormatterAgent to merge cross_reference_analysis into IdeaReport in packages/mcp-server/src/agents/formatter.py

### Extension UI (packages/extension)

- [x] T046 [US3] Display Cross-Reference Analysis section in side panel (convergences list, divergence cards with both agents' findings, deduplicated risks) in packages/extension/src/sidepanel/panel.ts

**Checkpoint**: User Story 3 complete — agents communicate and cross-reference findings

---

## Phase 6: User Story 4 - Configurable Data Sources and Agent Selection (Priority: P4)

**Goal**: Users can enable/disable individual agents and toggle external data lookups per agent

**Independent Test**: Disable News Agent in settings, trigger analysis, verify report has no News Context section

### Agent Config Storage (packages/extension)

- [x] T047 [US4] Add agent config storage (read/write AgentConfig[]) to packages/extension/src/lib/storage.ts
- [x] T048 [US4] Add default agent configs (all enabled, external data on) when no config exists in packages/extension/src/lib/storage.ts

### Options UI (packages/extension)

- [x] T049 [US4] Add "Data Agents" section to options page with per-agent enable/disable toggles in packages/extension/src/options/options.ts
- [x] T050 [US4] Add per-agent "Use web search" toggle in agent config section in packages/extension/src/options/options.ts
- [x] T051 [US4] Add NRP.ai as provider option with api_key and base_url fields in packages/extension/src/options/options.ts

### Coordinator Config Handling (packages/mcp-server)

- [x] T052 [US4] Update Coordinator to skip disabled agents based on agent_configs from UserSettings in packages/mcp-server/src/agents/collaborative/coordinator.py
- [x] T053 [US4] Update CollaborativeAgent to use LLM knowledge only (no tool calls) when use_external_data is false in packages/mcp-server/src/agents/collaborative/base.py
- [x] T054 [US4] Enforce UserSettings.web_lookup as master switch — when OFF, Coordinator disables all external data lookups regardless of per-agent use_external_data settings in packages/mcp-server/src/agents/collaborative/coordinator.py
- [x] T055 [US4] Handle graceful degradation in pipeline when all data agents are disabled (skip collaborative phase entirely) in packages/mcp-server/src/agents/pipeline.py

**Checkpoint**: User Story 4 complete — users control agent selection and data sources

---

## Phase 7: User Story 5 - Macro-Economic Context Agent (Priority: P5)

**Goal**: Macro Agent analyzes sector trends, economic indicators, headwinds/tailwinds and shares context with other agents

**Independent Test**: Select text about a tech company, verify report includes Macro Context section with sector trends and economic indicators

### Macro Agent (packages/mcp-server)

- [x] T056 [US5] Implement Macro Agent with web_search tool calling for sector/economic data and MacroAgentOutput in packages/mcp-server/src/agents/collaborative/macro.py
- [x] T057 [US5] Register Macro Agent in Coordinator agent list and wire its findings to Risk and Synthesis agents in packages/mcp-server/src/agents/collaborative/coordinator.py

### Pipeline & Formatter (packages/mcp-server)

- [x] T058 [US5] Extend FormatterAgent to merge macro_context into IdeaReport in packages/mcp-server/src/agents/formatter.py

### Extension UI (packages/extension)

- [x] T059 [US5] Display Macro Context section in side panel (sector, trends, indicators, headwinds, tailwinds) in packages/extension/src/sidepanel/panel.ts

**Checkpoint**: User Story 5 complete — macro-economic context enrichment available

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, edge cases, export support, and validation

### Error Handling

- [x] T060 [P] Handle NRP.ai endpoint unavailable with error message and retry option in packages/extension/src/popup/popup.ts
- [x] T061 [P] Handle agent timeout (individual agent exceeds response time) with graceful skip in packages/mcp-server/src/agents/collaborative/coordinator.py
- [x] T062 Handle context window overflow by summarizing intermediate agent outputs in packages/mcp-server/src/agents/collaborative/coordinator.py

### Edge Cases

- [x] T063 Handle no tickers identified — skip Fundamentals Agent, run News/Macro with keywords only in packages/mcp-server/src/agents/collaborative/coordinator.py
- [x] T064 Handle private company — Fundamentals Agent reports LLM knowledge only with clear data_source marking in packages/mcp-server/src/agents/collaborative/fundamentals.py

### Export Support

- [x] T065 [P] Extend Markdown export to include enrichment sections (News Context, Fundamentals, Cross-Reference, Macro) in packages/extension/src/lib/export.ts
- [x] T066 [P] Extend JSON export to include enrichment fields in packages/extension/src/lib/export.ts

### Validation

- [x] T067 Verify end-to-end enriched analysis flow per quickstart.md scenarios
- [x] T068 Verify graceful degradation when all agents disabled

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phases 3-7 (User Stories)**: All depend on Phase 2 completion
- **Phase 8 (Polish)**: Depends on all desired user stories complete

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US1 (Enriched Report) | Phase 2 only | — |
| US2 (Transparency) | Phase 2 only | US1 (uses enrichment data for labels) |
| US3 (Cross-Reference) | Phase 2 only | US1 (needs News+Fundamentals outputs) |
| US4 (Configuration) | Phase 2 only | US1, US2, US3 |
| US5 (Macro Agent) | Phase 2 only | US1, US2, US3, US4 |

### Within User Story Execution

1. Agent implementations (parallelizable)
2. Pipeline/coordinator integration
3. Extension UI components
4. Integration wiring

---

## Parallel Execution Examples

### Phase 2 — Models and schemas in parallel:
```
T004, T005 (Pydantic models — same file but independent sections)
T014, T015, T016, T017, T018, T019, T020 (JSON Schema files)
```

### Phase 3 (US1) — Agents in parallel:
```
T024, T025 (News Agent and Fundamentals Agent — different files)
T030, T031 (UI sections — different components)
```

### Phase 8 — Polish tasks in parallel:
```
T060, T061 (Error handling — different files)
T065, T066 (Export formats — same file but independent functions)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Enriched Report)
4. **STOP and VALIDATE**: Test enriched analysis end-to-end
5. Deploy if ready — users can get news + fundamentals enriched reports!

### Incremental Delivery

| Milestone | User Stories | Value Delivered |
|-----------|--------------|-----------------|
| MVP | US1 | Enriched reports with news + fundamentals |
| v0.2 | US1 + US2 | Agent transparency and attribution |
| v0.3 | US1-3 | Cross-referencing and divergence detection |
| v0.4 | US1-4 | User-configurable agent selection |
| v1.0 | US1-5 | Full multi-agent with macro context |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently testable
- Existing linear pipeline agents (extraction, entity, ticker, thesis, critique, confidence) are unchanged
- Collaborative agents live in separate `collaborative/` subdirectory for isolation
- Stop at any checkpoint to validate independently
