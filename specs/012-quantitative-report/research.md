# Research: Quantitative Investment Report

## Decision 1: Technical Indicator Calculation Source

**Decision**: Use yfinance for price history, calculate indicators locally

**Rationale**:
- yfinance already provides historical price data via `stock.history()`
- RSI and moving averages are simple calculations that don't need external APIs
- Keeps the system self-contained without additional dependencies

**Alternatives considered**:
- TA-Lib library: Adds complexity, requires C compilation
- External API (Alpha Vantage, Polygon): Rate limits, API keys, costs
- pandas-ta: Good but adds another dependency

## Decision 2: RSI Calculation Method

**Decision**: Standard 14-day RSI using Wilder's smoothing method

**Rationale**:
- Industry standard, widely recognized
- 14-day period is the default used by most charting platforms
- Wilder's method (exponential smoothing) is the original RSI formula

**Formula**:
```
RS = Average Gain / Average Loss (over 14 periods)
RSI = 100 - (100 / (1 + RS))
```

**Alternatives considered**:
- 7-day RSI: Too volatile for general use
- 21-day RSI: Too slow to react
- Simple average instead of Wilder's: Less accurate

## Decision 3: Moving Average Types

**Decision**: Simple Moving Averages (SMA) for 50-day and 200-day

**Rationale**:
- SMA is most commonly referenced in financial media
- 50 and 200-day are standard benchmarks (Golden Cross/Death Cross)
- Easy to understand for non-technical users

**Alternatives considered**:
- Exponential Moving Average (EMA): More responsive but less common in media
- Weighted Moving Average: More complex, less recognition
- 20-day/100-day: Less standard

## Decision 4: Price Performance Periods

**Decision**: 1-week, 1-month, 3-month, YTD percentage changes

**Rationale**:
- Covers short, medium, and calendar-year perspectives
- Aligns with common reporting standards
- Easy to calculate from price history

**Alternatives considered**:
- 1-day change: Too volatile, already available in most apps
- 6-month/1-year: Could add later, but 3-month + YTD covers key periods

## Decision 5: Sector Comparison Data

**Decision**: Use yfinance sector/industry classification with peer comparison

**Rationale**:
- yfinance provides sector and industry info via `stock.info`
- Can fetch sector ETF or peer companies for comparison
- No additional API needed

**Implementation approach**:
- Get sector from ticker info (e.g., "Technology")
- Compare P/E to sector median or use sector ETF as benchmark

**Alternatives considered**:
- Manual sector mapping: Too much maintenance
- Third-party sector data: Adds cost/complexity

## Decision 6: Confidence Score Removal Strategy

**Decision**: Make confidence_score optional with default None, deprecate in UI

**Rationale**:
- Breaking change if removed entirely - existing reports have it
- Making it optional allows backward compatibility
- UI simply stops displaying it

**Implementation**:
1. Change `confidence_score: float` to `confidence_score: float | None = None`
2. Change `confidence_explanation: str` to `confidence_explanation: str | None = None`
3. Update report generation to not populate these fields
4. Update UI to not render confidence section

**Alternatives considered**:
- Hard remove: Breaks API contract, existing saved reports
- Keep but hide: Wastes computation

## Decision 7: Data Model Location

**Decision**: Add TechnicalIndicators model to existing fundamentals.py

**Rationale**:
- Technical indicators are closely related to fundamental data
- Same provider (yfinance) retrieves both
- Keeps related models together

**Alternatives considered**:
- New technicals.py file: More files to manage
- Embed in idea_report.py: Too far from data source

## Decision 8: Caching Strategy for Technical Data

**Decision**: Cache technical indicators with 1-hour TTL (shorter than fundamentals)

**Rationale**:
- Technical indicators change throughout trading day
- 1-hour balance between freshness and API efficiency
- Can use existing SQLite cache infrastructure

**Alternatives considered**:
- No cache: Too many API calls
- Same 24-hour TTL as fundamentals: Data too stale for technical analysis
- Real-time: Overkill for report generation
