# Tasks: User Ticker Input

**Input**: Design documents from `/specs/010-user-ticker-input/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested. Manual testing per quickstart.md.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- Paths relative to `packages/extension/`

---

## Phase 1: Setup

**Purpose**: Type definitions and message schema updates

- [x] T001 Add UserTicker interface to src/types/index.ts
- [x] T002 Update IdeaRequest interface to include user_tickers in src/types/index.ts
- [x] T003 Update GenerateMessage payload type to include user_tickers in src/background/service-worker.ts

**Checkpoint**: Type system ready for implementation

---

## Phase 2: Foundational (Data Flow)

**Purpose**: Wire user_tickers through message passing and API calls

- [x] T004 Update handleGenerate to extract user_tickers from payload in src/background/service-worker.ts
- [x] T005 Update IdeaRequest construction to include user_tickers in src/background/service-worker.ts
- [x] T006 [P] Verify generateIdea passes user_tickers to backend in src/lib/api.ts
- [x] T007 [P] Verify generateIdeaStream passes user_tickers to backend in src/lib/api.ts

**Checkpoint**: Data flow complete — user_tickers reaches backend

---

## Phase 3: User Story 1 - Add Tickers Before Generation (Priority: P1) 🎯 MVP

**Goal**: Users can enter ticker symbols that appear as chips and are included in generated reports

**Independent Test**: Select text, add "AAPL" in ticker input, generate report, verify AAPL appears in report

### Implementation for User Story 1

- [x] T008 [US1] Add userTickers state array to PanelController class in src/sidepanel/panel.ts
- [x] T009 [US1] Add ticker input HTML markup to src/sidepanel/index.html
- [x] T010 [US1] Add renderTickerInput method to render input field and chips in src/sidepanel/panel.ts
- [x] T011 [US1] Add addTicker method to normalize input (uppercase, trim) and add chip in src/sidepanel/panel.ts
- [x] T012 [US1] Add removeTicker method to remove chip by index in src/sidepanel/panel.ts
- [x] T013 [US1] Add event listeners for Enter/comma/Tab/blur to trigger addTicker in src/sidepanel/panel.ts
- [x] T014 [US1] Add click handler on chip X button to trigger removeTicker in src/sidepanel/panel.ts
- [x] T015 [US1] Add deduplication logic in addTicker to prevent duplicate chips in src/sidepanel/panel.ts
- [x] T016 [US1] Wire Generate button to include userTickers in GENERATE message in src/sidepanel/panel.ts
- [x] T017 [US1] Add CSS styles for .ticker-input-container, .ticker-chip, .ticker-input in src/sidepanel/panel.ts (inline styles)
- [x] T018 [US1] Clear userTickers array after successful generation in src/sidepanel/panel.ts

**Checkpoint**: User Story 1 complete — tickers can be added and sent to backend

---

## Phase 4: User Story 2 - Ticker Validation Feedback (Priority: P2)

**Goal**: Users see visual feedback for invalid ticker formats; generation blocked if invalid tickers exist

**Independent Test**: Enter "invalid123456789", verify red/error chip style, verify Generate button disabled

### Implementation for User Story 2

- [x] T019 [US2] Add isValid property to TickerChip interface in src/sidepanel/panel.ts
- [x] T020 [US2] Add validateTicker function with regex ^[A-Z0-9.\-]{1,12}$ in src/sidepanel/panel.ts
- [x] T021 [US2] Update addTicker to set isValid based on validateTicker result in src/sidepanel/panel.ts
- [x] T022 [US2] Add .ticker-chip.invalid CSS class with error styling in src/sidepanel/panel.ts
- [x] T023 [US2] Update renderTickerInput to apply invalid class based on isValid in src/sidepanel/panel.ts
- [x] T024 [US2] Add hasInvalidTickers check before Generate in src/sidepanel/panel.ts
- [x] T025 [US2] Disable Generate button and show tooltip when invalid tickers exist in src/sidepanel/panel.ts

**Checkpoint**: User Story 2 complete — validation feedback works

---

## Phase 5: User Story 3 - Ticker Autocomplete (Priority: P3)

**Goal**: Users can search by company name and select from suggestions

**Independent Test**: Type "Apple", see "AAPL - Apple Inc." suggestion, click to add chip

### Implementation for User Story 3

- [x] T026 [US3] Add autocomplete API endpoint call to backend ticker_search in src/lib/api.ts
- [x] T027 [US3] Add debounced input handler for autocomplete trigger in src/sidepanel/panel.ts
- [x] T028 [US3] Add suggestions dropdown HTML and rendering logic in src/sidepanel/panel.ts
- [x] T029 [US3] Add click handler on suggestion to add as chip with company_name in src/sidepanel/panel.ts
- [x] T030 [US3] Add CSS styles for .ticker-suggestions dropdown in src/sidepanel/panel.ts
- [x] T031 [US3] Add keyboard navigation (arrow keys, enter) for suggestions in src/sidepanel/panel.ts
- [x] T032 [US3] Handle network errors gracefully (hide suggestions, allow manual entry) in src/sidepanel/panel.ts

**Checkpoint**: User Story 3 complete — autocomplete functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Report display and edge cases

- [x] T033 Update renderTickers to show "(user)" indicator for user-provided tickers in src/sidepanel/panel.ts
- [x] T034 Add .user-provided CSS class for visual distinction in report in src/sidepanel/panel.ts
- [x] T035 Test international ticker formats (.KS, .T, .HK) pass validation
- [x] T036 Verify empty ticker input preserves existing behavior (LLM-only detection)
- [ ] T037 Manual test: run quickstart.md validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion
- **User Stories (Phase 3-5)**: All depend on Phase 2 completion
- **Polish (Phase 6)**: Depends on Phase 3 (US1) minimum; all stories for full polish

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 2 — enhances US1 but independently testable
- **User Story 3 (P3)**: Can start after Phase 2 — independent of US1/US2

### Parallel Opportunities

- T006, T007 can run in parallel (different functions in api.ts)
- T008-T018 (US1) are mostly sequential within panel.ts (same file)
- US1, US2, US3 could be worked in parallel by different developers
- T033, T034, T035, T036 can run in parallel (different concerns)

---

## Parallel Example: Foundational Phase

```bash
# Can run in parallel (different files/functions):
Task: T006 - Verify generateIdea passes user_tickers
Task: T007 - Verify generateIdeaStream passes user_tickers
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T007)
3. Complete Phase 3: User Story 1 (T008-T018)
4. **STOP and VALIDATE**: Test adding tickers and generating report
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → Deploy (MVP!)
3. Add User Story 2 → Test validation feedback → Deploy
4. Add User Story 3 → Test autocomplete → Deploy
5. Polish phase → Final testing

---

## Notes

- All US1 tasks modify panel.ts — execute sequentially to avoid conflicts
- Backend already supports user_tickers — no server changes needed
- P3 (autocomplete) requires new API endpoint; defer if time constrained
- Commit after each phase checkpoint for easy rollback
