# API Contracts: Quantitative Investment Report

## New Endpoints

### GET /api/v1/technicals/{ticker}

Get technical indicators for a single ticker.

**Request**:
```
GET /api/v1/technicals/AAPL
```

**Response** (200 OK):
```json
{
  "ticker": "AAPL",
  "current_price": 251.45,
  "ma_50": 245.32,
  "ma_200": 218.67,
  "rsi_14": 58.4,
  "price_change_1w": 0.023,
  "price_change_1m": 0.087,
  "price_change_3m": 0.152,
  "price_change_ytd": 0.234,
  "volume_avg_10d": 52340000,
  "retrieved_at": "2026-03-24T12:00:00Z",
  "data_source": "yfinance"
}
```

**Response** (404 Not Found):
```json
{
  "error": "Ticker not found or no price data available"
}
```

### GET /api/v1/quantitative/{ticker}

Get combined quantitative report (fundamentals + technicals + valuation).

**Request**:
```
GET /api/v1/quantitative/AAPL
```

**Response** (200 OK):
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "fundamentals": {
    "pe_ratio": 31.83,
    "forward_pe": 26.99,
    "market_cap": "$3.7T",
    "dividend_yield": 0.0041,
    "eps": 7.90,
    "revenue": "$435.6B",
    "revenue_growth": 0.157,
    "profit_margin": 0.2704,
    "fifty_two_week_high": "$288.62",
    "fifty_two_week_low": "$169.21"
  },
  "technicals": {
    "current_price": 251.45,
    "ma_50": 245.32,
    "ma_200": 218.67,
    "rsi_14": 58.4,
    "price_change_1w": 0.023,
    "price_change_1m": 0.087,
    "price_change_3m": 0.152,
    "price_change_ytd": 0.234
  },
  "valuation": {
    "sector": "Technology",
    "pe_ratio": 31.83,
    "sector_pe_avg": 28.5,
    "pe_vs_sector": "above"
  },
  "data_sources": ["yfinance"],
  "retrieved_at": "2026-03-24T12:00:00Z"
}
```

### POST /api/v1/quantitative/batch

Get quantitative data for multiple tickers.

**Request**:
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"]
}
```

**Response** (200 OK):
```json
{
  "AAPL": { /* QuantitativeReport */ },
  "MSFT": { /* QuantitativeReport */ },
  "GOOGL": { /* QuantitativeReport */ }
}
```

## Modified Endpoints

### POST /api/v1/ideas (Modified)

**Response changes**:
- `confidence_score` field now optional (may be null)
- `confidence_explanation` field now optional (may be null)
- New `quantitative_data` array added

**Before**:
```json
{
  "confidence_score": 0.75,
  "confidence_explanation": "High confidence based on...",
  ...
}
```

**After**:
```json
{
  "confidence_score": null,
  "confidence_explanation": null,
  "quantitative_data": [
    {
      "ticker": "AAPL",
      "fundamentals": { ... },
      "technicals": { ... },
      "valuation": { ... }
    }
  ],
  ...
}
```

### POST /api/v1/ideas/stream (Modified)

Same response structure changes as `/api/v1/ideas`.

## Error Responses

All endpoints return standard error format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Status Codes**:
- 200: Success
- 400: Invalid request (bad ticker format)
- 404: Ticker not found
- 500: Internal server error
- 504: Timeout (data provider took too long)
