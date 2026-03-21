# Tasks: Smart Ticker Discovery

**Input**: Design documents from `/specs/009-smart-ticker-discovery/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **MCP Server**: `packages/mcp-server/src/`
- **Extension**: `packages/extension/src/`
- **Tests**: `packages/mcp-server/tests/`

---

## Phase 1: Setup

**Purpose**: No new project initialization needed — extending existing TickerAgent

- [x] T001 Verify existing ticker.py structure in packages/mcp-server/src/agents/ticker.py
- [x] T002 [P] Verify existing agent_outputs.py structure in packages/mcp-server/src/models/agent_outputs.py
- [x] T003 [P] Verify existing ticker_search.py tools in packages/mcp-server/src/tools/ticker_search.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Add ConfidenceLevel enum to packages/mcp-server/src/models/agent_outputs.py
- [x] T005 Add Sector model to packages/mcp-server/src/models/agent_outputs.py
- [x] T006 Add InferredTicker model to packages/mcp-server/src/models/agent_outputs.py
- [x] T007 Extend TickerOutput with sectors and inferred_tickers fields in packages/mcp-server/src/models/agent_outputs.py
- [x] T008 Add SectorInferenceOutput model for internal LLM response in packages/mcp-server/src/models/agent_outputs.py
- [x] T009 Update pipeline.py to pass cleaned_text to TickerAgent in packages/mcp-server/src/agents/pipeline.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Sector-Aware Ticker Inference (Priority: P1) 🎯 MVP

**Goal**: System identifies sectors from text and infers relevant companies even when no companies are explicitly mentioned

**Independent Test**: Select text about "AI chip demand" with no company names. System should return at least 3 relevant semiconductor companies with tickers.

### Implementation for User Story 1

- [x] T010 [US1] Add sector inference system prompt extension to TickerAgent.get_system_prompt() in packages/mcp-server/src/agents/ticker.py
- [x] T011 [US1] Add sector inference user prompt method _get_sector_inference_prompt() in packages/mcp-server/src/agents/ticker.py
- [x] T012 [US1] Implement _infer_from_sectors() async method in TickerAgent in packages/mcp-server/src/agents/ticker.py
- [x] T013 [US1] Implement _filter_low_confidence() method to exclude low confidence tickers in packages/mcp-server/src/agents/ticker.py
- [x] T014 [US1] Implement _verify_inferred_tickers() method using existing ticker_search.py tools in packages/mcp-server/src/agents/ticker.py
- [x] T015 [US1] Implement _deduplicate_tickers() method to merge inferred with mentioned in packages/mcp-server/src/agents/ticker.py
- [x] T016 [US1] Update TickerAgent.run() to call sector inference when cleaned_text is provided in packages/mcp-server/src/agents/ticker.py
- [x] T017 [US1] Handle graceful fallback when no sectors identified in packages/mcp-server/src/agents/ticker.py

**Checkpoint**: User Story 1 complete - sector inference returns at least 3 companies for recognizable sectors

---

## Phase 4: User Story 2 - Expert-Level Sector Decomposition (Priority: P2)

**Goal**: System decomposes complex themes into sub-sectors and identifies companies across supply chain layers

**Independent Test**: Select text about "AI infrastructure spending" and verify system returns companies across multiple supply chain layers (chips, cloud, networking, power)

### Implementation for User Story 2

- [x] T018 [US2] Enhance sector inference prompt to identify sub-sectors and supply chain layers in packages/mcp-server/src/agents/ticker.py
- [x] T019 [US2] Update Sector model prompt handling to populate sub_sectors field in packages/mcp-server/src/agents/ticker.py
- [x] T020 [US2] Update InferredTicker prompt handling to populate supply_chain_layer field in packages/mcp-server/src/agents/ticker.py
- [x] T021 [US2] Add validation to ensure at least 2 supply chain layers for complex themes in packages/mcp-server/src/agents/ticker.py

**Checkpoint**: User Story 2 complete - complex themes return companies across multiple supply chain layers

---

## Phase 5: User Story 3 - Market-Localized Expert Knowledge (Priority: P2)

**Goal**: System prioritizes local-exchange companies when text is in a specific language

**Independent Test**: Select Korean-language text about semiconductors and verify Korean-listed tickers (005930.KS, 000660.KS) appear with higher relevance

### Implementation for User Story 3

- [x] T022 [US3] Pass language hint to sector inference prompt from settings.output_language in packages/mcp-server/src/agents/ticker.py
- [x] T023 [US3] Update sector inference prompt to prioritize local exchange companies based on language in packages/mcp-server/src/agents/ticker.py
- [x] T024 [US3] Ensure market_hint is passed to yfinance verification for local exchange lookup in packages/mcp-server/src/agents/ticker.py

**Checkpoint**: User Story 3 complete - non-English text prioritizes local exchange tickers

---

## Phase 6: User Story 4 - Confidence-Weighted Inferred Tickers (Priority: P3)

**Goal**: Inferred tickers are clearly distinguished from mentioned tickers with relevance explanations

**Independent Test**: Generate report from text mentioning one company. Verify mentioned tickers are labeled differently from inferred sector peers, and each inferred ticker has an explanation.

### Implementation for User Story 4

- [x] T025 [US4] Ensure relevance_explanation is required and populated for all inferred tickers in packages/mcp-server/src/agents/ticker.py
- [x] T026 [US4] Update FormatterAgent to display inferred tickers separately from mentioned tickers in packages/mcp-server/src/agents/formatter.py
- [x] T027 [US4] Add source label ("mentioned" vs "inferred") display logic in report formatting in packages/mcp-server/src/agents/formatter.py
- [x] T028 [US4] Display relevance explanation for each inferred ticker in report in packages/mcp-server/src/agents/formatter.py
- [x] T029 [US4] Display verified/unverified status for inferred tickers in report in packages/mcp-server/src/agents/formatter.py

**Checkpoint**: User Story 4 complete - users can distinguish mentioned from inferred tickers at a glance

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, performance, and cleanup

- [x] T030 Handle edge case: text too vague to identify any sector (return empty inferred_tickers) in packages/mcp-server/src/agents/ticker.py
- [x] T031 Handle edge case: sector has no publicly traded pure-play companies in packages/mcp-server/src/agents/ticker.py
- [x] T032 Handle edge case: text discusses multiple unrelated sectors in packages/mcp-server/src/agents/ticker.py
- [x] T033 Implement async parallel verification calls for inferred tickers to meet latency budget in packages/mcp-server/src/agents/ticker.py
- [x] T034 Add logging for sector inference operations in packages/mcp-server/src/agents/ticker.py
- [ ] T035 Run quickstart.md validation scenarios manually

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verification only
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Core sector inference - can start after Foundational
- **User Story 2 (P2)**: Builds on US1 prompts - can run in parallel but benefits from US1 completion
- **User Story 3 (P2)**: Builds on US1 prompts - can run in parallel but benefits from US1 completion
- **User Story 4 (P3)**: Depends on US1 output structure - needs US1 complete for integration

### Within Each User Story

- Models/prompts before logic
- Logic before integration
- Core implementation before edge cases

### Parallel Opportunities

- T001, T002, T003 can run in parallel (verification tasks)
- T004, T005, T006, T007, T008 are sequential (model dependencies)
- Once Foundational completes, US1/US2/US3 can theoretically run in parallel
- T030, T031, T032 can run in parallel (independent edge cases)

---

## Parallel Example: Foundational Phase

```bash
# These verification tasks can run in parallel:
Task: "Verify existing ticker.py structure"
Task: "Verify existing agent_outputs.py structure"
Task: "Verify existing ticker_search.py tools"
```

## Parallel Example: Polish Phase

```bash
# These edge case tasks can run in parallel:
Task: "Handle edge case: text too vague"
Task: "Handle edge case: sector has no pure-play companies"
Task: "Handle edge case: multiple unrelated sectors"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify existing code)
2. Complete Phase 2: Foundational (add models, update pipeline)
3. Complete Phase 3: User Story 1 (sector inference core)
4. **STOP and VALIDATE**: Test with "AI chip demand" text
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → MVP ready!
3. Add User Story 2 → Test supply chain decomposition
4. Add User Story 3 → Test localization
5. Add User Story 4 → Test report formatting
6. Polish → Edge cases and performance

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All changes are localized to TickerAgent and FormatterAgent - no new agents needed
