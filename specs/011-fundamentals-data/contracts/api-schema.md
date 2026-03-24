# API Contract: Fundamentals Data

**Feature**: 011-fundamentals-data
**Date**: 2026-03-24

## Endpoints

### GET /api/v1/fundamentals/{ticker}

Retrieve fundamental data for a single ticker.

**Request**:
```
GET /api/v1/fundamentals/AAPL
GET /api/v1/fundamentals/005930.KS
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| refresh | boolean | No | Force cache refresh (default: false) |

**Response 200**:
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "exchange": "NASDAQ",
  "currency": "USD",
  "metrics": {
    "pe_ratio": 28.5,
    "forward_pe": 26.2,
    "market_cap": "$2.8T",
    "market_cap_raw": 2800000000000,
    "dividend_yield": 0.005,
    "eps": 6.42,
    "forward_eps": 6.85,
    "fifty_two_week_high": "$199.62",
    "fifty_two_week_low": "$164.08",
    "revenue": "$383.3B",
    "revenue_growth": 0.08,
    "profit_margin": 0.26
  },
  "source": "yfinance",
  "retrieved_at": "2026-03-24T10:30:00Z",
  "data_unavailable": false,
  "cached": true,
  "cache_expires_at": "2026-03-25T10:30:00Z"
}
```

**Response 200 (Data Unavailable)**:
```json
{
  "ticker": "INVALID123",
  "company_name": "",
  "exchange": "",
  "currency": "USD",
  "metrics": {},
  "source": "unavailable",
  "retrieved_at": "2026-03-24T10:30:00Z",
  "data_unavailable": true,
  "error_message": "Ticker not found in any data source",
  "cached": false
}
```

**Response 400**:
```json
{
  "error": "invalid_ticker",
  "message": "Ticker format invalid. Expected: 1-12 alphanumeric characters with optional suffix"
}
```

---

### POST /api/v1/fundamentals/batch

Retrieve fundamental data for multiple tickers.

**Request**:
```json
{
  "tickers": ["AAPL", "MSFT", "005930.KS"],
  "refresh": false
}
```

**Response 200**:
```json
{
  "results": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "metrics": { ... },
      "source": "yfinance",
      "data_unavailable": false
    },
    {
      "ticker": "MSFT",
      "company_name": "Microsoft Corporation",
      "metrics": { ... },
      "source": "cache",
      "data_unavailable": false
    },
    {
      "ticker": "005930.KS",
      "company_name": "Samsung Electronics Co., Ltd.",
      "metrics": { ... },
      "source": "yfinance",
      "data_unavailable": false
    }
  ],
  "summary": {
    "total": 3,
    "successful": 3,
    "failed": 0,
    "from_cache": 1
  }
}
```

---

### GET /api/v1/fundamentals/{ticker}/history

Retrieve historical metrics for trend analysis (P3).

**Request**:
```
GET /api/v1/fundamentals/AAPL/history?metrics=pe_ratio,revenue&periods=4
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| metrics | string | No | Comma-separated list (default: pe_ratio,eps) |
| periods | integer | No | Number of quarters (default: 4, max: 8) |

**Response 200**:
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "trends": [
    {
      "metric_name": "pe_ratio",
      "data_points": [
        { "period": "Q4 2025", "date": "2025-12-31", "value": 28.5 },
        { "period": "Q3 2025", "date": "2025-09-30", "value": 30.2 },
        { "period": "Q2 2025", "date": "2025-06-30", "value": 29.1 },
        { "period": "Q1 2025", "date": "2025-03-31", "value": 27.8 }
      ]
    },
    {
      "metric_name": "revenue",
      "data_points": [
        { "period": "Q4 2025", "date": "2025-12-31", "value": 119500000000 },
        { "period": "Q3 2025", "date": "2025-09-30", "value": 94900000000 },
        { "period": "Q2 2025", "date": "2025-06-30", "value": 85800000000 },
        { "period": "Q1 2025", "date": "2025-03-31", "value": 90800000000 }
      ]
    }
  ],
  "source": "yfinance"
}
```

---

### DELETE /api/v1/fundamentals/cache

Clear cache (admin/debug endpoint).

**Request**:
```json
{
  "tickers": ["AAPL"],  // Optional: specific tickers
  "all": false          // Optional: clear entire cache
}
```

**Response 200**:
```json
{
  "cleared": 1,
  "message": "Cache cleared for 1 ticker(s)"
}
```

---

## Internal Provider Interface

### FundamentalsProvider (Abstract)

```python
class FundamentalsProvider(ABC):
    name: str
    priority: int
    supported_markets: list[str]

    @abstractmethod
    async def get_fundamentals(self, ticker: str) -> FundamentalData | None:
        """Retrieve fundamental data for a ticker."""
        pass

    @abstractmethod
    async def get_historical(self, ticker: str, periods: int) -> list[HistoricalTrend]:
        """Retrieve historical metrics (optional)."""
        pass

    def supports_market(self, ticker: str) -> bool:
        """Check if provider supports the ticker's market."""
        pass
```

### Provider Priority Chain

```python
PROVIDER_CHAIN = [
    YFinanceProvider(priority=1),   # Primary
    InvestpyProvider(priority=2),   # Secondary
    ScraperProvider(priority=3),    # Tertiary
]
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| invalid_ticker | 400 | Ticker format doesn't match expected pattern |
| provider_error | 502 | All data providers failed |
| rate_limited | 429 | Too many requests, retry after delay |
| cache_error | 500 | Internal cache error |

---

## Rate Limiting

| Provider | Limit | Backoff |
|----------|-------|---------|
| yfinance | 2000/hour | Exponential (1s, 2s, 4s) |
| investpy | 100/hour | Linear (10s between requests) |
| scraper | 30/hour | Linear (30s between requests) |

Internal API rate limit: 60 requests/minute per client.
