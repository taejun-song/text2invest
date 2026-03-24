# Tasks: Fundamentals Data Retrieval

**Input**: Design documents from `/specs/011-fundamentals-data/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested. Manual testing per quickstart.md.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- Paths relative to `packages/mcp-server/`

---

## Phase 1: Setup

**Purpose**: Add dependencies and create directory structure

- [x] T001 Add investpy and aiosqlite to pyproject.toml dependencies
- [x] T002 [P] Create src/providers/fundamentals/ directory structure
- [x] T003 [P] Create src/storage/ directory structure
- [x] T004 [P] Create data/ directory for SQLite database file

**Checkpoint**: Dependencies installed, directories ready

---

## Phase 2: Foundational (Data Models & Base Infrastructure)

**Purpose**: Core models and abstract interfaces needed by all user stories

- [x] T005 Add FundamentalMetrics model in src/models/fundamentals.py
- [x] T006 Add DataSourceType enum and FundamentalData model in src/models/fundamentals.py
- [x] T007 [P] Create abstract FundamentalsProvider base class in src/providers/fundamentals/base.py
- [x] T008 [P] Add format_currency and format_large_number helpers in src/providers/fundamentals/formatters.py
- [x] T009 Update FundamentalsSnapshot in src/models/collaborative.py to include fundamental_data field
- [x] T010 Create __init__.py exports in src/providers/fundamentals/__init__.py
- [x] T011 [P] Create __init__.py in src/storage/__init__.py

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - View Stock Fundamentals in Report (Priority: P1) MVP

**Goal**: Display real fundamental data (P/E, market cap, dividend yield, 52-week range) in generated reports

**Independent Test**: Generate a report for AAPL, verify fundamental metrics appear with real values

### Implementation for User Story 1

- [x] T012 [US1] Implement YFinanceProvider.get_fundamentals() in src/providers/fundamentals/yfinance_provider.py
- [x] T013 [US1] Add yfinance data extraction and normalization to FundamentalMetrics format in src/providers/fundamentals/yfinance_provider.py
- [x] T014 [US1] Implement InvestpyProvider.get_fundamentals() in src/providers/fundamentals/investpy_provider.py
- [x] T015 [US1] Implement ScraperProvider.get_fundamentals() stub in src/providers/fundamentals/scraper_provider.py
- [x] T016 [US1] Create FundamentalsService with priority chain logic in src/providers/fundamentals/service.py
- [x] T017 [US1] Add timeout handling (5s yfinance, 5s investpy, 3s scraper) in src/providers/fundamentals/service.py
- [x] T018 [US1] Update FundamentalsAgent to use FundamentalsService in src/agents/collaborative/fundamentals.py
- [x] T019 [US1] Add GET /api/v1/fundamentals/{ticker} endpoint in src/api_server.py
- [x] T020 [US1] Add POST /api/v1/fundamentals/batch endpoint in src/api_server.py
- [x] T021 [US1] Handle invalid ticker gracefully with data_unavailable=True in src/providers/fundamentals/service.py
- [x] T022 [US1] Add currency formatting for international markets in src/providers/fundamentals/formatters.py

**Checkpoint**: User Story 1 complete - real fundamentals appear in reports

---

## Phase 4: User Story 2 - Cached Fundamentals for Faster Reports (Priority: P2)

**Goal**: Cache fundamental data locally with 24-hour TTL to reduce API calls

**Independent Test**: Generate two reports for AAPL within 24 hours, verify second uses cached data

### Implementation for User Story 2

- [x] T023 [US2] Implement FundamentalsCache with SQLite in src/storage/fundamentals_cache.py
- [x] T024 [US2] Add cache initialization (create tables) in src/storage/fundamentals_cache.py
- [x] T025 [US2] Implement get_cached(ticker) method in src/storage/fundamentals_cache.py
- [x] T026 [US2] Implement set_cached(ticker, data, ttl) method in src/storage/fundamentals_cache.py
- [x] T027 [US2] Implement is_expired(ticker) check in src/storage/fundamentals_cache.py
- [x] T028 [US2] Implement delete_cached(ticker) method in src/storage/fundamentals_cache.py
- [x] T029 [US2] Implement clear_all() method for cache reset in src/storage/fundamentals_cache.py
- [x] T030 [US2] Integrate cache lookup before provider chain in src/providers/fundamentals/service.py
- [x] T031 [US2] Integrate cache write after successful provider fetch in src/providers/fundamentals/service.py
- [x] T032 [US2] Add cache fallback when storage unavailable in src/providers/fundamentals/service.py
- [x] T033 [US2] Add ?refresh=true query param to bypass cache in GET /api/v1/fundamentals/{ticker}
- [x] T034 [US2] Add DELETE /api/v1/fundamentals/cache endpoint in src/api_server.py
- [x] T035 [US2] Add cached=true/false and cache_expires_at to API response in src/api_server.py

**Checkpoint**: User Story 2 complete - caching reduces API calls

---

## Phase 5: User Story 3 - Historical Data Comparison (Priority: P3)

**Goal**: Display quarterly trends for P/E ratio and revenue

**Independent Test**: View a report for AAPL, see 1-year trend for key metrics

### Implementation for User Story 3

- [x] T036 [US3] Add HistoricalMetric and HistoricalTrend models in src/models/fundamentals.py
- [x] T037 [US3] Add historical_metrics table to SQLite schema in src/storage/fundamentals_cache.py
- [x] T038 [US3] Implement YFinanceProvider.get_historical() using quarterly_financials in src/providers/fundamentals/yfinance_provider.py
- [x] T039 [US3] Add get_historical_cached() method in src/storage/fundamentals_cache.py
- [x] T040 [US3] Add set_historical_cached() method in src/storage/fundamentals_cache.py
- [x] T041 [US3] Integrate historical data into FundamentalsService in src/providers/fundamentals/service.py
- [x] T042 [US3] Add GET /api/v1/fundamentals/{ticker}/history endpoint in src/api_server.py
- [x] T043 [US3] Update FundamentalsSnapshot to include historical_trends field in src/models/collaborative.py
- [x] T044 [US3] Handle missing historical data gracefully (return current snapshot only) in src/providers/fundamentals/service.py

**Checkpoint**: User Story 3 complete - historical trends displayed

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, logging, and edge cases

- [x] T045 Add rate limiting tracking per provider in src/providers/fundamentals/service.py
- [x] T046 Add exponential backoff for yfinance (1s, 2s, 4s) in src/providers/fundamentals/yfinance_provider.py
- [x] T047 Add linear backoff for investpy (10s between requests) in src/providers/fundamentals/investpy_provider.py
- [x] T048 [P] Add logging for all provider calls and failures in src/providers/fundamentals/service.py
- [x] T049 [P] Add logging for cache hits/misses in src/storage/fundamentals_cache.py
- [x] T050 Handle SQLite database corruption with auto-recreate in src/storage/fundamentals_cache.py
- [x] T051 Verify international ticker formats (.KS, .T, .HK, .L, .DE) work correctly
- [x] T052 Manual test: run quickstart.md validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion
- **User Stories (Phase 3-5)**: All depend on Phase 2 completion
- **Polish (Phase 6)**: Depends on Phase 3 (US1) minimum; all stories for full polish

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 2 - Enhances US1 but independently testable
- **User Story 3 (P3)**: Can start after Phase 2 - Extends US1/US2 but independently testable

### Parallel Opportunities

- T002, T003, T004 can run in parallel (different directories)
- T007, T008, T010, T011 can run in parallel (different files)
- T012-T015 provider implementations can run in parallel
- T023-T029 cache methods can be implemented sequentially within same file
- T045-T050 polish tasks can run in parallel (different concerns)

---

## Parallel Example: Provider Implementations

```bash
# Launch all provider implementations in parallel:
Task: T012 - YFinanceProvider.get_fundamentals()
Task: T014 - InvestpyProvider.get_fundamentals()
Task: T015 - ScraperProvider.get_fundamentals() stub
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T011)
3. Complete Phase 3: User Story 1 (T012-T022)
4. **STOP and VALIDATE**: Generate report for AAPL, verify real fundamentals appear
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → Deploy (MVP!)
3. Add User Story 2 → Test caching → Deploy
4. Add User Story 3 → Test historical trends → Deploy
5. Polish phase → Final testing

---

## Notes

- yfinance is already in pyproject.toml - verify version compatibility
- investpy may have sporadic maintenance - implement robust fallback
- SQLite database location: `packages/mcp-server/data/fundamentals.db`
- All monetary values display in native currency with symbol
- Cache TTL: 24 hours default
- Provider timeouts: yfinance 5s, investpy 5s, scraper 3s
