# Data Model: Quantitative Investment Report

## New Models

### TechnicalIndicators

Calculated price-based indicators for a ticker.

```python
class TechnicalIndicators(BaseModel):
    ticker: str
    current_price: float | None
    ma_50: float | None           # 50-day simple moving average
    ma_200: float | None          # 200-day simple moving average
    rsi_14: float | None          # 14-day RSI (0-100)
    price_change_1w: float | None # 1-week % change
    price_change_1m: float | None # 1-month % change
    price_change_3m: float | None # 3-month % change
    price_change_ytd: float | None # Year-to-date % change
    volume_avg_10d: int | None    # 10-day average volume
    retrieved_at: datetime
    data_source: str = "yfinance"
```

**Validation Rules**:
- RSI must be between 0 and 100
- Price changes are decimals (0.05 = 5%)
- All fields optional to handle missing data gracefully

### ValuationComparison

Stock valuation relative to sector.

```python
class ValuationComparison(BaseModel):
    ticker: str
    sector: str
    pe_ratio: float | None
    sector_pe_avg: float | None
    pe_vs_sector: str | None      # "above", "below", "at"
    forward_pe: float | None
    sector_forward_pe_avg: float | None
```

### QuantitativeReport

Combined quantitative data for report.

```python
class QuantitativeReport(BaseModel):
    ticker: str
    company_name: str
    fundamentals: FundamentalMetrics  # Existing model
    technicals: TechnicalIndicators
    valuation: ValuationComparison | None
    data_sources: list[str]
    retrieved_at: datetime
```

## Modified Models

### IdeaReport (idea_report.py)

Changes to existing model:

```python
# BEFORE
confidence_score: float = Field(..., ge=0, le=1)
confidence_explanation: str = Field(...)

# AFTER
confidence_score: float | None = Field(None, ge=0, le=1, deprecated=True)
confidence_explanation: str | None = Field(None, deprecated=True)
quantitative_data: list[QuantitativeReport] = Field(default_factory=list)
```

### FundamentalsSnapshot (collaborative.py)

Add technical indicators to snapshot:

```python
class FundamentalsSnapshot(BaseModel):
    # ... existing fields ...
    technical_indicators: dict | None = Field(None, description="Technical analysis data")
```

## Cache Schema Extension

Add to SQLite schema (fundamentals_cache.py):

```sql
CREATE TABLE IF NOT EXISTS technical_cache (
    ticker TEXT PRIMARY KEY,
    data TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    expires_at TEXT NOT NULL  -- 1 hour TTL
);
```

## Entity Relationships

```
IdeaReport
    └── quantitative_data: list[QuantitativeReport]
            ├── fundamentals: FundamentalMetrics (existing)
            ├── technicals: TechnicalIndicators (new)
            └── valuation: ValuationComparison (new)
```

## State Transitions

None - all models are data containers without state machines.
