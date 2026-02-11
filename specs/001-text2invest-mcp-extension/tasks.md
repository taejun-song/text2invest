# Tasks: Text2Invest

**Input**: Design documents from `/specs/001-text2invest-mcp-extension/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **packages/core/**: Shared schemas and types (JSON Schema, TypeScript)
- **packages/mcp-server/**: Python FastMCP server
- **packages/extension/**: Chrome Extension (MV3, TypeScript)

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create monorepo structure and configure build tools

- [x] T001 Create monorepo directory structure per plan.md (packages/core, packages/mcp-server, packages/extension)
- [x] T002 [P] Initialize packages/mcp-server with pyproject.toml for Python 3.13 and dependencies (fastmcp, litellm, pydantic)
- [x] T003 [P] Initialize packages/extension with package.json and TypeScript config
- [x] T004 [P] Initialize packages/core with package.json for shared schemas
- [x] T005 [P] Configure ruff and black for Python linting/formatting in packages/mcp-server/
- [x] T006 [P] Configure ESLint and Prettier for TypeScript in packages/extension/
- [x] T007 Create root pyproject.toml with uv workspace configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core schemas and infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Shared Schemas (packages/core)

- [x] T008 [P] Define IdeaReport JSON Schema in packages/core/src/schemas/idea-report.json
- [x] T009 [P] Define Ticker JSON Schema in packages/core/src/schemas/ticker.json
- [x] T010 [P] Define RationaleQuote JSON Schema in packages/core/src/schemas/rationale-quote.json
- [x] T011 [P] Define Source JSON Schema in packages/core/src/schemas/source.json
- [x] T012 [P] Define ProviderMeta JSON Schema in packages/core/src/schemas/provider-meta.json
- [x] T013 [P] Define UserSettings JSON Schema in packages/core/src/schemas/user-settings.json
- [x] T014 [P] Define Evaluation JSON Schema in packages/core/src/schemas/evaluation.json
- [x] T015 Create schema index and validation utilities in packages/core/src/validators/index.ts

### MCP Server Foundation (packages/mcp-server)

- [x] T016 [P] Create Pydantic models from schemas in packages/mcp-server/src/models/idea_report.py
- [x] T017 [P] Create Pydantic models for agent outputs in packages/mcp-server/src/models/agent_outputs.py
- [x] T018 Implement LiteLLM provider wrapper in packages/mcp-server/src/providers/llm.py
- [x] T019 Create FastMCP server entry point with health endpoint in packages/mcp-server/src/server.py
- [x] T020 Implement request cancellation manager in packages/mcp-server/src/tools/cancellation.py

### Extension Foundation (packages/extension)

- [x] T021 Create manifest.json with MV3 configuration, minimal permissions, side_panel in packages/extension/src/manifest.json
- [x] T022 [P] Generate TypeScript types from JSON Schemas in packages/extension/src/types/
- [x] T023 [P] Implement chrome.storage.local wrapper in packages/extension/src/lib/storage.ts
- [x] T024 Implement MCP server API client in packages/extension/src/lib/api.ts
- [x] T025 Create service worker with message handling in packages/extension/src/background/service-worker.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Generate Investment Idea (Priority: P1) 🎯 MVP

**Goal**: User selects text, clicks "Generate idea", receives structured investment report within 30 seconds

**Independent Test**: Select text on any webpage, trigger generation, verify valid IdeaReport returned with tickers, thesis, confidence

### Agent Pipeline (packages/mcp-server)

- [x] T026 [P] [US1] Implement Extraction Agent in packages/mcp-server/src/agents/extraction.py
- [x] T027 [P] [US1] Implement Entity Agent in packages/mcp-server/src/agents/entity.py
- [x] T028 [P] [US1] Implement Ticker Agent in packages/mcp-server/src/agents/ticker.py
- [x] T029 [P] [US1] Implement Thesis Agent in packages/mcp-server/src/agents/thesis.py
- [x] T030 [P] [US1] Implement Critique Agent in packages/mcp-server/src/agents/critique.py
- [x] T031 [P] [US1] Implement Confidence Agent in packages/mcp-server/src/agents/confidence.py
- [x] T032 [P] [US1] Implement Formatter Agent in packages/mcp-server/src/agents/formatter.py
- [x] T033 [US1] Create pipeline orchestrator with retry logic in packages/mcp-server/src/agents/pipeline.py
- [x] T034 [US1] Implement generate_idea MCP tool in packages/mcp-server/src/tools/generate_idea.py
- [x] T035 [US1] Add POST /api/v1/ideas endpoint to server in packages/mcp-server/src/server.py

### Extension Content Script (packages/extension)

- [x] T036 [US1] Implement text selection detection with 600ms debounce in packages/extension/src/content/selection.ts
- [x] T037 [US1] Enforce min 20 chars, max 8,000 chars with truncation notice in packages/extension/src/content/selection.ts
- [x] T038 [US1] Implement PII redaction (emails, phones) in packages/extension/src/content/selection.ts

### Extension Popup (packages/extension)

- [x] T039 [US1] Create popup HTML structure in packages/extension/src/popup/index.html
- [x] T040 [US1] Implement popup logic with "Generate idea" button in packages/extension/src/popup/popup.ts
- [x] T041 [US1] Add loading indicator and cancel button to popup in packages/extension/src/popup/popup.ts
- [x] T042 [US1] Handle generation states (idle, generating, completed, failed) in packages/extension/src/popup/popup.ts

### Service Worker Integration (packages/extension)

- [x] T043 [US1] Wire content script → service worker → MCP server flow in packages/extension/src/background/service-worker.ts
- [x] T044 [US1] Implement request cancellation via POST /api/v1/ideas/{id}/cancel in packages/extension/src/background/service-worker.ts
- [x] T045 [US1] Store completed reports in chrome.storage.local in packages/extension/src/background/service-worker.ts

**Checkpoint**: User Story 1 complete - can generate investment ideas from selected text

---

## Phase 4: User Story 2 - View Full Report (Priority: P2)

**Goal**: User opens side panel to view complete report with all sections, expandable, with disclaimer

**Independent Test**: Generate a report, click "Open full report", verify all sections present with correct data

### Side Panel UI (packages/extension)

- [x] T046 [US2] Create side panel HTML structure in packages/extension/src/sidepanel/index.html
- [x] T047 [US2] Implement report viewer component in packages/extension/src/sidepanel/panel.ts
- [x] T048 [US2] Display executive summary (max 3 bullets) in packages/extension/src/sidepanel/panel.ts
- [x] T049 [US2] Display tickers with confidence scores in packages/extension/src/sidepanel/panel.ts
- [x] T050 [US2] Display rationale quotes with text highlighting in packages/extension/src/sidepanel/panel.ts
- [x] T051 [US2] Display catalysts, risks, counter-thesis sections in packages/extension/src/sidepanel/panel.ts
- [x] T052 [US2] Display horizon and confidence with explanation in packages/extension/src/sidepanel/panel.ts
- [x] T053 [US2] Add collapsible provider metadata section in packages/extension/src/sidepanel/panel.ts
- [x] T054 [US2] Add mandatory disclaimer "Educational only - Not financial advice" in packages/extension/src/sidepanel/panel.ts

### Popup Integration (packages/extension)

- [x] T055 [US2] Add "Open full report" button to popup (when report ready) in packages/extension/src/popup/popup.ts
- [x] T056 [US2] Wire popup to open side panel via chrome.sidePanel API in packages/extension/src/popup/popup.ts

**Checkpoint**: User Story 2 complete - can view full reports in side panel

---

## Phase 5: User Story 3 - History & Search (Priority: P3)

**Goal**: User browses history, searches by ticker/site/date, re-opens past reports

**Independent Test**: Generate 3+ reports, search for specific ticker, verify correct results appear

### History Storage (packages/extension)

- [x] T057 [US3] Implement report indexing for search in packages/extension/src/lib/storage.ts
- [x] T058 [US3] Add ticker, domain, date extraction for indexing in packages/extension/src/lib/storage.ts

### History UI (packages/extension)

- [x] T059 [US3] Create history view section in side panel in packages/extension/src/sidepanel/panel.ts
- [x] T060 [US3] Implement report list with reverse chronological order in packages/extension/src/sidepanel/panel.ts
- [x] T061 [US3] Add search input with ticker/site/date filtering in packages/extension/src/sidepanel/panel.ts
- [x] T062 [US3] Wire history item click to open full report in packages/extension/src/sidepanel/panel.ts

**Checkpoint**: User Story 3 complete - can search and browse report history

---

## Phase 6: User Story 4 - Export Report (Priority: P4)

**Goal**: User exports report as Markdown or JSON file with all sections and disclaimer

**Independent Test**: Generate report, export as Markdown, verify .md file contains all sections; repeat for JSON

### Export Utilities (packages/extension)

- [x] T063 [P] [US4] Implement Markdown export formatter in packages/extension/src/lib/export.ts
- [x] T064 [P] [US4] Implement JSON export formatter in packages/extension/src/lib/export.ts
- [x] T065 [US4] Add download trigger using Blob and URL.createObjectURL in packages/extension/src/lib/export.ts

### Export UI (packages/extension)

- [x] T066 [US4] Add export buttons (Markdown, JSON) to report view in packages/extension/src/sidepanel/panel.ts
- [x] T067 [US4] Ensure disclaimer included in both export formats in packages/extension/src/lib/export.ts

**Checkpoint**: User Story 4 complete - can export reports in Markdown and JSON

---

## Phase 7: User Story 5 - Configure LLM Provider (Priority: P5)

**Goal**: User configures provider (OpenAI/Anthropic/Ollama), model, temperature, API key

**Independent Test**: Configure Anthropic, generate idea, verify Anthropic model used in provider_meta

### Options Page (packages/extension)

- [x] T068 [US5] Create options HTML structure in packages/extension/src/options/index.html
- [x] T069 [US5] Implement provider selection dropdown in packages/extension/src/options/options.ts
- [x] T070 [US5] Add API key input (masked, for cloud providers) in packages/extension/src/options/options.ts
- [x] T071 [US5] Add base URL input for Ollama in packages/extension/src/options/options.ts
- [x] T072 [US5] Add model name input in packages/extension/src/options/options.ts
- [x] T073 [US5] Add temperature slider (0-2) in packages/extension/src/options/options.ts
- [x] T074 [US5] Add PII redaction toggle (default ON) in packages/extension/src/options/options.ts
- [x] T075 [US5] Save settings to chrome.storage.local in packages/extension/src/options/options.ts
- [x] T076 [US5] Validate settings (require API key for cloud, base_url for Ollama) in packages/extension/src/options/options.ts

### Settings Integration (packages/extension)

- [x] T077 [US5] Pass user settings to MCP server in generate request in packages/extension/src/background/service-worker.ts
- [x] T078 [US5] Block generation if no provider configured (prompt to settings) in packages/extension/src/popup/popup.ts

### MCP Server Provider Support (packages/mcp-server)

- [x] T079 [US5] Configure LiteLLM for OpenAI in packages/mcp-server/src/providers/llm.py
- [x] T080 [US5] Configure LiteLLM for Anthropic in packages/mcp-server/src/providers/llm.py
- [x] T081 [US5] Configure LiteLLM for Ollama in packages/mcp-server/src/providers/llm.py

**Checkpoint**: User Story 5 complete - can configure and use different LLM providers

---

## Phase 8: User Story 6 - Rating & Feedback (Priority: P6)

**Goal**: User rates reports as useful/not useful with optional notes, stored locally

**Independent Test**: Rate a report "useful", verify rating persisted in storage

### Evaluation API (packages/mcp-server)

- [x] T082 [US6] Add POST /api/v1/evaluation endpoint in packages/mcp-server/src/server.py
- [x] T083 [US6] Store evaluation with idea_id reference in packages/mcp-server/src/server.py

### Rating UI (packages/extension)

- [x] T084 [US6] Add thumbs up/down rating buttons to report view in packages/extension/src/sidepanel/panel.ts
- [x] T085 [US6] Add optional notes textarea (shown after rating) in packages/extension/src/sidepanel/panel.ts
- [x] T086 [US6] Submit rating to MCP server and store locally in packages/extension/src/sidepanel/panel.ts
- [x] T087 [US6] Display existing rating if report was previously rated in packages/extension/src/sidepanel/panel.ts

**Checkpoint**: User Story 6 complete - can rate and provide feedback on reports

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, edge cases, and final improvements

### Error Handling

- [x] T088 [P] Handle LLM provider unreachable with retry option in packages/extension/src/popup/popup.ts
- [x] T089 [P] Handle rate limit errors with wait time display in packages/extension/src/popup/popup.ts
- [x] T090 [P] Handle schema validation failures after 3 retries in packages/mcp-server/src/agents/base.py
- [x] T091 Handle navigation-away cancellation in packages/extension/src/content/selection.ts

### Edge Cases

- [x] T092 Handle empty tickers (no companies found) with low confidence in packages/mcp-server/src/agents/ticker.py
- [x] T093 Handle text > 8,000 chars with truncation notice in packages/extension/src/content/selection.ts

### Documentation

- [x] T094 [P] Update quickstart.md with actual commands and test instructions
- [x] T095 [P] Add inline code comments for complex agent prompts

### Validation

- [ ] T096 Verify end-to-end flow per quickstart.md scenarios
- [ ] T097 Verify extension works on Chrome and Edge browsers

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phases 3-8 (User Stories)**: All depend on Phase 2 completion
- **Phase 9 (Polish)**: Depends on all desired user stories complete

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US1 (Generate) | Phase 2 only | - |
| US2 (View Report) | Phase 2 only | US1 (but needs report data) |
| US3 (History) | Phase 2 only | US1, US2 |
| US4 (Export) | Phase 2 only | US1, US2, US3 |
| US5 (Provider Config) | Phase 2 only | US1, US2, US3, US4 |
| US6 (Rating) | Phase 2 only | US1, US2, US3, US4, US5 |

### Within User Story Execution

1. Agent implementations (parallelizable)
2. Pipeline orchestration
3. UI components (parallelizable)
4. Integration wiring

---

## Parallel Execution Examples

### Phase 2 - All schemas in parallel:
```
T008, T009, T010, T011, T012, T013, T014 (JSON Schema files)
T016, T017 (Pydantic models)
T022, T023 (TypeScript types, storage)
```

### Phase 3 (US1) - All agents in parallel:
```
T026, T027, T028, T029, T030, T031, T032 (7 agent implementations)
```

### Phase 4 (US2) - Report sections in parallel:
```
T048, T049, T050, T051, T052, T053 (display components)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Generate Investment Idea)
4. **STOP and VALIDATE**: Test generation end-to-end
5. Deploy if ready - users can generate ideas!

### Incremental Delivery

| Milestone | User Stories | Value Delivered |
|-----------|--------------|-----------------|
| MVP | US1 | Generate investment ideas |
| v0.2 | US1 + US2 | View full structured reports |
| v0.3 | US1-3 | History and search |
| v0.4 | US1-4 | Export for external use |
| v0.5 | US1-5 | Multi-provider support |
| v1.0 | US1-6 | Complete with feedback loop |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently testable
- Commit after each task or logical group
- All 7 agents can be developed in parallel (Phase 3)
- Stop at any checkpoint to validate independently
