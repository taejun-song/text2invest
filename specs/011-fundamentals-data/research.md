# Research: Fundamentals Data Retrieval

**Feature**: 011-fundamentals-data
**Date**: 2026-03-24

## Decision 1: Primary Data Source (yfinance)

**Decision**: Use yfinance as the primary data source for fundamental data.

**Rationale**:
- Already in codebase (`yfinance>=0.2.0` in pyproject.toml)
- Provides comprehensive fundamental data via `Ticker.info` property
- Supports global markets (US, Korea `.KS`, Japan `.T`, Europe)
- No API key required, free to use
- Active maintenance and community support

**Alternatives considered**:
- Alpha Vantage: Requires API key, rate limits on free tier (5/min)
- Finnhub: Requires API key, limited free data
- Yahoo Finance direct scraping: More fragile than yfinance wrapper

**Data available via yfinance**:
- `trailingPE`, `forwardPE` - P/E ratios
- `marketCap` - Market capitalization
- `dividendYield` - Dividend yield
- `trailingEps`, `forwardEps` - EPS
- `fiftyTwoWeekHigh`, `fiftyTwoWeekLow` - 52-week range
- `totalRevenue`, `revenueGrowth` - Revenue metrics
- `currency` - Native currency

## Decision 2: Secondary Data Source (investpy)

**Decision**: Use investpy as fallback when yfinance fails.

**Rationale**:
- Scrapes investing.com which has broad international coverage
- Good for markets where yfinance has gaps (some European exchanges)
- Can retrieve historical data for trend analysis

**Alternatives considered**:
- Direct investing.com API: No official API available
- Financial Modeling Prep: Requires paid subscription for global data

**Limitations**:
- May be rate-limited by investing.com
- Data structure differs from yfinance, requires normalization
- Library maintenance has been sporadic

## Decision 3: Tertiary Data Source (Web Scraping)

**Decision**: Implement lightweight scraping for specific edge cases.

**Rationale**:
- Fallback when both yfinance and investpy fail
- Target specific reliable sources (company investor relations pages)
- Keep scope limited to avoid maintenance burden

**Implementation approach**:
- Use existing web_search tool for news-based data extraction
- Parse structured data from known reliable sources
- Mark data_source as "web_scraping" for transparency

## Decision 4: Cache Strategy (SQLite)

**Decision**: SQLite with 24-hour TTL for fundamental data caching.

**Rationale**:
- Fundamental data doesn't change frequently (daily at most)
- 24-hour TTL balances freshness vs. API call reduction
- SQLite is lightweight, file-based, perfect for single-user scenario
- Already standard in Python, no additional dependencies needed
- aiosqlite provides async support for non-blocking operations

**Schema design**:
```sql
CREATE TABLE fundamentals_cache (
    ticker TEXT PRIMARY KEY,
    data JSON NOT NULL,
    source TEXT NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_expires ON fundamentals_cache(expires_at);
```

**Alternatives considered**:
- Redis: Overkill for single-user, requires separate process
- In-memory dict: Lost on restart, no persistence
- File-based JSON: Slower for lookups, harder to query

## Decision 5: Data Normalization

**Decision**: Normalize all data sources to a common FundamentalData model.

**Rationale**:
- Each source returns data in different formats
- Agent and UI should work with consistent data shape
- Easier to add new sources without changing consumers

**Normalization rules**:
- Always use ticker in Yahoo format (e.g., `005930.KS` for Samsung)
- Convert all monetary values to strings with currency symbol
- Use ISO 8601 for all timestamps
- Map source-specific field names to canonical names

## Decision 6: Error Handling Strategy

**Decision**: Graceful degradation with partial data fallback.

**Rationale**:
- Report generation should never fail due to fundamentals
- Users get best available data, clearly marked with source
- Transparent about data quality and availability

**Implementation**:
1. Try yfinance first (timeout: 5s)
2. If fails, try investpy (timeout: 5s)
3. If fails, try web scraping (timeout: 3s)
4. If all fail, return empty snapshot with `data_unavailable=True`
5. Always continue report generation
6. Log failures for monitoring

## Decision 7: Historical Data Approach

**Decision**: Store quarterly snapshots when available, display trends in UI.

**Rationale**:
- yfinance provides some historical metrics via `quarterly_financials`
- Useful for showing P/E ratio trends, revenue growth
- P3 priority - implement basic version first

**Data to capture**:
- Quarterly revenue (last 4 quarters)
- Quarterly EPS (last 4 quarters)
- P/E ratio at each quarter end (if available)

## Decision 8: International Market Support

**Decision**: Prioritize markets based on exchange suffix detection.

**Markets and suffixes**:
| Market | Suffix | Example |
|--------|--------|---------|
| US (NYSE/NASDAQ) | none | AAPL |
| Korea KOSPI | .KS | 005930.KS |
| Korea KOSDAQ | .KQ | 035720.KQ |
| Japan TSE | .T | 7203.T |
| Hong Kong | .HK | 0700.HK |
| UK LSE | .L | SHEL.L |
| Germany XETRA | .DE | SAP.DE |

**Currency handling**:
- Display in stock's native currency
- Include currency label (e.g., "Market Cap: ₩412.5T")
- No currency conversion (out of scope)
