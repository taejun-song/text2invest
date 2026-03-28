# Tasks: Quantitative Investment Report

**Input**: Design documents from `/specs/012-quantitative-report/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested. Manual testing per quickstart.md.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- Paths relative to `packages/mcp-server/`

---

## Phase 1: Setup

**Purpose**: No new dependencies needed - using existing yfinance

- [x] T001 Verify yfinance already installed in pyproject.toml

**Checkpoint**: Dependencies confirmed

---

## Phase 2: Foundational (Data Models & Base Infrastructure)

**Purpose**: Core models needed by all user stories

- [x] T002 Add TechnicalIndicators model in src/models/fundamentals.py
- [x] T003 [P] Add ValuationComparison model in src/models/fundamentals.py
- [x] T004 [P] Add QuantitativeReport model in src/models/fundamentals.py
- [x] T005 Make confidence_score and confidence_explanation optional in src/models/idea_report.py
- [x] T006 Add quantitative_data field to IdeaReport in src/models/idea_report.py
- [x] T007 Add technical_indicators field to FundamentalsSnapshot in src/models/collaborative.py
- [x] T008 Add technical_cache table to SQLite schema in src/storage/fundamentals_cache.py

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - View Quantitative Metrics in Report (Priority: P1) MVP

**Goal**: Display real fundamental data prominently in reports, remove confidence score from output

**Independent Test**: Generate a report for AAPL, verify fundamental metrics appear and confidence_score is null

### Implementation for User Story 1

- [x] T009 [US1] Implement get_technical_indicators() in src/providers/fundamentals/yfinance_provider.py
- [x] T010 [US1] Add calculate_rsi() helper function in src/providers/fundamentals/yfinance_provider.py
- [x] T011 [US1] Add calculate_moving_averages() helper in src/providers/fundamentals/yfinance_provider.py
- [x] T012 [US1] Add calculate_price_changes() helper in src/providers/fundamentals/yfinance_provider.py
- [x] T013 [US1] Add get_technical_indicators() to FundamentalsService in src/providers/fundamentals/service.py
- [x] T014 [US1] Add technical data caching (1-hour TTL) in src/providers/fundamentals/service.py
- [x] T015 [US1] Update FundamentalsAgent.run_with_real_data() to include technical indicators in src/agents/collaborative/fundamentals.py
- [x] T016 [US1] Add GET /api/v1/technicals/{ticker} endpoint in src/api_server.py
- [x] T017 [US1] Add GET /api/v1/quantitative/{ticker} endpoint in src/api_server.py
- [x] T018 [US1] Add POST /api/v1/quantitative/batch endpoint in src/api_server.py
- [x] T019 [US1] Update Pipeline to not populate confidence_score in src/agents/pipeline.py
- [x] T020 [US1] Update report display in extension to show quantitative metrics in packages/extension/src/sidepanel/panel.ts
- [x] T021 [US1] Hide confidence score section in UI in packages/extension/src/sidepanel/panel.ts

**Checkpoint**: User Story 1 complete - fundamental metrics displayed, confidence score removed

---

## Phase 4: User Story 2 - View Technical Indicators (Priority: P2)

**Goal**: Display moving averages, RSI, and price momentum in reports

**Independent Test**: Generate a report for MSFT, verify MA50, MA200, RSI values appear

### Implementation for User Story 2

- [x] T022 [US2] Add technical indicators section to report display in packages/extension/src/sidepanel/panel.ts
- [x] T023 [US2] Format RSI with overbought/oversold indicators (>70 / <30) in packages/extension/src/sidepanel/panel.ts
- [x] T024 [US2] Format moving averages with price position indicator (above/below MA) in packages/extension/src/sidepanel/panel.ts
- [x] T025 [US2] Format price changes as percentages with color coding in packages/extension/src/sidepanel/panel.ts
- [x] T026 [US2] Handle missing technical data gracefully in UI in packages/extension/src/sidepanel/panel.ts

**Checkpoint**: User Story 2 complete - technical indicators displayed with formatting

---

## Phase 5: User Story 3 - Valuation Comparison (Priority: P3)

**Goal**: Show stock P/E vs sector average

**Independent Test**: Generate a report for GOOGL, verify sector comparison appears

### Implementation for User Story 3

- [x] T027 [US3] Implement get_sector_info() in src/providers/fundamentals/yfinance_provider.py
- [x] T028 [US3] Implement get_valuation_comparison() in src/providers/fundamentals/service.py
- [x] T029 [US3] Include valuation comparison in QuantitativeReport output in src/providers/fundamentals/service.py
- [x] T030 [US3] Add valuation comparison section to report display in packages/extension/src/sidepanel/panel.ts
- [x] T031 [US3] Format P/E vs sector with above/below/at indicator in packages/extension/src/sidepanel/panel.ts

**Checkpoint**: User Story 3 complete - valuation comparison displayed

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, edge cases, validation

- [x] T032 [P] Handle missing data gracefully with "N/A" display in src/providers/fundamentals/service.py
- [x] T033 [P] Add data source attribution to quantitative output in src/providers/fundamentals/service.py
- [x] T034 [P] Handle international tickers with different currencies in src/providers/fundamentals/yfinance_provider.py
- [x] T035 [P] Add logging for technical indicator calculations in src/providers/fundamentals/yfinance_provider.py
- [x] T036 Manual test: run quickstart.md validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - confirm existing setup
- **Foundational (Phase 2)**: Depends on Phase 1 completion
- **User Stories (Phase 3-5)**: All depend on Phase 2 completion
- **Polish (Phase 6)**: Depends on Phase 3 (US1) minimum

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 - Core metrics and confidence removal
- **User Story 2 (P2)**: Can start after Phase 2 - Technical indicators display (builds on US1 UI)
- **User Story 3 (P3)**: Can start after Phase 2 - Valuation comparison (independent feature)

### Parallel Opportunities

- T002, T003, T004 can run in parallel (different model additions)
- T009-T012 can run in parallel (different helper functions)
- T022-T026 can run in parallel (different UI sections)
- T032-T035 can run in parallel (different concerns)

---

## Parallel Example: Technical Indicator Helpers

```bash
# Launch all helper implementations in parallel:
Task: T010 - calculate_rsi() helper
Task: T011 - calculate_moving_averages() helper
Task: T012 - calculate_price_changes() helper
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify dependencies)
2. Complete Phase 2: Foundational (models)
3. Complete Phase 3: User Story 1 (metrics + remove confidence)
4. **STOP and VALIDATE**: Generate report for AAPL, verify metrics appear
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → Deploy (MVP!)
3. Add User Story 2 → Test technical indicators → Deploy
4. Add User Story 3 → Test valuation comparison → Deploy
5. Polish phase → Final testing

---

## Notes

- yfinance already provides price history via `stock.history()`
- RSI calculation: 14-day Wilder's smoothing method
- Moving averages: Simple MA (SMA) for 50 and 200 days
- Technical cache TTL: 1 hour (shorter than 24h fundamentals cache)
- Confidence score made optional, not removed, for backward compatibility
