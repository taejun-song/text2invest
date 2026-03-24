# Data Model: Fundamentals Data Retrieval

**Feature**: 011-fundamentals-data
**Date**: 2026-03-24

## Entity Relationship

```
┌─────────────────────┐       ┌─────────────────────┐
│  FundamentalData    │       │   CachedFundamental │
├─────────────────────┤       ├─────────────────────┤
│ ticker: str         │──────▶│ ticker: str (PK)    │
│ company_name: str   │       │ data: JSON          │
│ exchange: str       │       │ source: str         │
│ currency: str       │       │ fetched_at: datetime│
│ metrics: Metrics    │       │ expires_at: datetime│
│ source: DataSource  │       └─────────────────────┘
│ retrieved_at: dt    │
│ data_unavailable: bool
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│   FundamentalMetrics│
├─────────────────────┤
│ pe_ratio: float?    │
│ forward_pe: float?  │
│ market_cap: str     │
│ dividend_yield: float?
│ eps: float?         │
│ forward_eps: float? │
│ fifty_two_week_high: str
│ fifty_two_week_low: str
│ revenue: str?       │
│ revenue_growth: float?
│ profit_margin: float?
└─────────────────────┘
```

## Pydantic Models

### FundamentalMetrics

Core financial metrics normalized across all data sources.

```python
class FundamentalMetrics(BaseModel):
    pe_ratio: float | None = Field(None, description="Trailing P/E ratio")
    forward_pe: float | None = Field(None, description="Forward P/E ratio")
    market_cap: str | None = Field(None, description="Market cap with currency (e.g., '$2.8T')")
    market_cap_raw: int | None = Field(None, description="Market cap in base currency units")
    dividend_yield: float | None = Field(None, description="Dividend yield as decimal (0.02 = 2%)")
    eps: float | None = Field(None, description="Trailing EPS")
    forward_eps: float | None = Field(None, description="Forward EPS estimate")
    fifty_two_week_high: str | None = Field(None, description="52-week high with currency")
    fifty_two_week_low: str | None = Field(None, description="52-week low with currency")
    revenue: str | None = Field(None, description="Total revenue with currency")
    revenue_growth: float | None = Field(None, description="Revenue growth YoY as decimal")
    profit_margin: float | None = Field(None, description="Profit margin as decimal")
```

### FundamentalData

Complete fundamental data for a single ticker.

```python
class DataSourceType(str, Enum):
    YFINANCE = "yfinance"
    INVESTPY = "investpy"
    WEB_SCRAPING = "web_scraping"
    CACHE = "cache"
    UNAVAILABLE = "unavailable"

class FundamentalData(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Full company name")
    exchange: str = Field("", description="Exchange name")
    currency: str = Field("USD", description="Native currency code")
    metrics: FundamentalMetrics = Field(default_factory=FundamentalMetrics)
    source: DataSourceType = Field(..., description="Data source used")
    retrieved_at: datetime = Field(..., description="When data was retrieved")
    data_unavailable: bool = Field(False, description="True if no data could be retrieved")
    error_message: str | None = Field(None, description="Error details if unavailable")
```

### HistoricalMetric

For P3: Historical trend data.

```python
class HistoricalMetric(BaseModel):
    period: str = Field(..., description="Period label (e.g., 'Q1 2025')")
    date: date = Field(..., description="Period end date")
    value: float = Field(..., description="Metric value")

class HistoricalTrend(BaseModel):
    metric_name: str = Field(..., description="Name of metric (e.g., 'P/E Ratio')")
    data_points: list[HistoricalMetric] = Field(default_factory=list)
```

### CachedFundamental

SQLite cache entry structure.

```python
class CachedFundamental(BaseModel):
    ticker: str = Field(..., description="Primary key")
    data: FundamentalData = Field(..., description="Cached fundamental data")
    source: DataSourceType = Field(..., description="Original data source")
    fetched_at: datetime = Field(..., description="When originally fetched")
    expires_at: datetime = Field(..., description="Cache expiration time")
```

## Updated FundamentalsSnapshot

Update existing model in `models/collaborative.py` to use new structure:

```python
class FundamentalsSnapshot(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Full company name")
    exchange: str = Field("", description="Exchange name")
    currency: str = Field("USD", description="Native currency code")
    metrics: list[FinancialMetric] = Field(default_factory=list)
    # New fields
    fundamental_data: FundamentalData | None = Field(None, description="Structured fundamental data")
    historical_trends: list[HistoricalTrend] = Field(default_factory=list)
    data_source: DataSource = Field(..., description="How this data was obtained")
    retrieved_at: datetime = Field(..., description="When data was retrieved")
```

## SQLite Schema

```sql
-- Main cache table
CREATE TABLE IF NOT EXISTS fundamentals_cache (
    ticker TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    exchange TEXT,
    currency TEXT DEFAULT 'USD',
    data JSON NOT NULL,
    source TEXT NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

-- Index for cache expiration queries
CREATE INDEX IF NOT EXISTS idx_fundamentals_expires
ON fundamentals_cache(expires_at);

-- Historical data table (P3)
CREATE TABLE IF NOT EXISTS historical_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    period TEXT NOT NULL,
    period_date DATE NOT NULL,
    value REAL NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    UNIQUE(ticker, metric_name, period)
);

CREATE INDEX IF NOT EXISTS idx_historical_ticker
ON historical_metrics(ticker);
```

## Validation Rules

1. **Ticker format**: Must match pattern `^[A-Z0-9.\\-]{1,12}$`
2. **Currency**: Must be valid ISO 4217 code (USD, KRW, JPY, EUR, etc.)
3. **Percentages**: Store as decimals (0.02 = 2%), display with % symbol
4. **Large numbers**: Format with appropriate suffix (K, M, B, T)
5. **Cache TTL**: Default 24 hours, configurable per data source

## State Transitions

```
┌─────────────┐
│   UNKNOWN   │ Initial state - ticker not in cache
└──────┬──────┘
       │ fetch requested
       ▼
┌─────────────┐
│  FETCHING   │ Attempting to retrieve data
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌──────┐ ┌──────────┐
│CACHED│ │UNAVAILABLE│
└──┬───┘ └──────────┘
   │ TTL expires
   ▼
┌─────────────┐
│   STALE     │ Needs refresh
└──────┬──────┘
       │ refresh requested
       ▼
┌─────────────┐
│  FETCHING   │ (loop back)
└─────────────┘
```
