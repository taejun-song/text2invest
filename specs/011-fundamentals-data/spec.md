# Feature Specification: Fundamentals Data Retrieval

**Feature Branch**: `011-fundamentals-data`
**Created**: 2026-03-24
**Status**: Draft
**Input**: User description: "investpy project for retrieving data from investing.com or scraping, with SQLite storage for fundamental data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Stock Fundamentals in Report (Priority: P1)

When generating an investment report, users want to see real fundamental data (P/E ratio, market cap, dividend yield, etc.) alongside the AI-generated thesis to make more informed decisions.

**Why this priority**: Core value proposition - enriching AI-generated reports with actual financial data makes them significantly more useful for investment decisions.

**Independent Test**: Generate a report for AAPL, verify fundamental metrics appear in the enrichment section with actual values (not placeholders).

**Acceptance Scenarios**:

1. **Given** a user generates a report for a US stock (e.g., AAPL), **When** the fundamentals agent runs, **Then** the report displays P/E ratio, market cap, 52-week high/low, and dividend yield with real values.
2. **Given** a user generates a report for a Korean stock (e.g., 005930.KS), **When** the fundamentals agent runs, **Then** the report displays localized fundamental metrics appropriate for that market.
3. **Given** a user generates a report for an invalid ticker, **When** the fundamentals agent runs, **Then** the system gracefully handles the error and continues report generation without fundamentals data.

---

### User Story 2 - Cached Fundamentals for Faster Reports (Priority: P2)

Users want reports to generate quickly. By caching fundamental data locally, subsequent reports for the same ticker can skip external API calls and use stored data.

**Why this priority**: Performance optimization - reduces API rate limiting issues and speeds up report generation for frequently analyzed stocks.

**Independent Test**: Generate two reports for the same ticker within 24 hours, verify the second report completes faster and uses cached data.

**Acceptance Scenarios**:

1. **Given** fundamental data for AAPL was fetched within the last 24 hours, **When** a new report for AAPL is generated, **Then** the system uses cached data without external API calls.
2. **Given** cached data for AAPL is older than 24 hours, **When** a new report for AAPL is generated, **Then** the system fetches fresh data and updates the cache.
3. **Given** the cache storage is unavailable, **When** a report is generated, **Then** the system falls back to live API calls without failing.

---

### User Story 3 - Historical Data Comparison (Priority: P3)

Users want to see how key metrics have changed over time (e.g., P/E ratio trend, revenue growth) to understand the company's trajectory.

**Why this priority**: Enhanced analysis - provides temporal context but not essential for basic report functionality.

**Independent Test**: View a report and see a 1-year trend for key metrics like P/E ratio and revenue.

**Acceptance Scenarios**:

1. **Given** a report is generated for AAPL, **When** historical data is available, **Then** the report shows quarterly trends for P/E ratio and revenue over the past year.
2. **Given** historical data is not available for a ticker, **When** the report is generated, **Then** only current snapshot data is shown without errors.

---

### Edge Cases

- What happens when investing.com blocks or rate-limits requests? System should gracefully degrade and use cached data or skip fundamentals.
- How does the system handle tickers not found on investing.com? System should mark the ticker as "fundamentals unavailable" and continue.
- What happens when the SQLite database is corrupted? System should recreate the database and continue operation.
- How does the system handle currency differences for international stocks? Values should be displayed in the stock's native currency with clear labels.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST retrieve fundamental data (P/E, market cap, 52-week range, dividend yield, EPS) for stock tickers.
- **FR-002**: System MUST support multiple markets including US (NYSE, NASDAQ), Korea (KOSPI, KOSDAQ), Japan (TSE), and major European exchanges.
- **FR-003**: System MUST cache retrieved fundamental data locally to reduce external API dependency.
- **FR-004**: System MUST refresh cached data when older than 24 hours.
- **FR-005**: System MUST handle data retrieval failures gracefully without blocking report generation.
- **FR-006**: System MUST display fundamental data in the report's enrichment section.
- **FR-007**: System MUST support retrieving historical fundamental data (quarterly snapshots) for trend analysis.
- **FR-008**: System MUST clearly indicate when fundamental data is unavailable for a ticker.
- **FR-009**: System MUST respect rate limits of data sources to avoid being blocked.
- **FR-010**: System MUST display monetary values in the stock's native currency with appropriate labels.
- **FR-011**: System MUST use a priority chain for data retrieval: yfinance (primary) → investpy (secondary) → web scraping (tertiary), attempting each source in sequence until successful.

### Key Entities

- **FundamentalSnapshot**: Point-in-time financial metrics for a stock (ticker, date, P/E, market cap, dividend yield, EPS, 52-week high/low, volume).
- **StockMetadata**: Basic stock information (ticker, company name, exchange, currency, sector, industry).
- **DataSource**: Configuration for where to retrieve data (source name, priority, rate limits, supported markets).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Fundamental data appears in 90% of generated reports for supported exchanges.
- **SC-002**: Cached data reduces external API calls by 70% for frequently analyzed tickers.
- **SC-003**: Report generation time increases by no more than 3 seconds when fetching fresh fundamental data.
- **SC-004**: System recovers gracefully from data source failures with 100% report completion rate (with or without fundamentals).
- **SC-005**: Users can see at least 4 key metrics (P/E, market cap, dividend yield, 52-week range) for any supported stock.

## Assumptions

- yfinance (already in codebase) provides adequate fundamental data for most tickers; investpy and scraping serve as fallbacks.
- Rate limiting from data sources can be managed with appropriate delays and caching.
- A 24-hour cache TTL is acceptable for fundamental data (not real-time trading use case).
- SQLite is sufficient for local storage needs (single-user Chrome extension context).
- The fundamentals agent already exists in the codebase and needs to be enhanced with real data sources.

## Out of Scope

- Real-time price data or streaming quotes
- Options or derivatives data
- Full financial statements (income statement, balance sheet, cash flow)
- Premium data sources requiring paid subscriptions
- Multi-user data sharing or synchronization

## Clarifications

### Session 2026-03-24

- Q: Data source fallback strategy when one source fails? → A: Multiple sources with priority chain (yfinance → investpy → scraping)
