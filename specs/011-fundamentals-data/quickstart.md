# Quickstart: Fundamentals Data Retrieval

**Feature**: 011-fundamentals-data
**Date**: 2026-03-24

## Prerequisites

- Python 3.13+ with uv
- MCP server running (`uv run uvicorn src.api_server:app`)
- Chrome extension loaded

## Setup

### 1. Install New Dependencies

```bash
cd packages/mcp-server
uv add investpy aiosqlite
uv sync
```

### 2. Initialize SQLite Database

The database will be auto-created on first use at `packages/mcp-server/data/fundamentals.db`.

To verify:
```bash
cd packages/mcp-server
python -c "from src.storage.fundamentals_cache import FundamentalsCache; import asyncio; asyncio.run(FundamentalsCache().init())"
```

### 3. Restart MCP Server

```bash
cd packages/mcp-server
uv run uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload
```

## Validation Scenarios

### US1: View Stock Fundamentals in Report

**Test: Generate report for US stock**
1. Open Chrome extension sidepanel
2. Select text mentioning Apple or AAPL
3. Click "Generate"
4. Verify report shows:
   - P/E Ratio (e.g., 28.5)
   - Market Cap (e.g., $2.8T)
   - Dividend Yield (e.g., 0.5%)
   - 52-Week Range (e.g., $164.08 - $199.62)

**Test: Generate report for Korean stock**
1. Select text mentioning "삼성전자" (Samsung Electronics)
2. Verify ticker resolves to 005930.KS
3. Verify fundamentals show in KRW currency

**Test: Invalid ticker gracefully handled**
1. Manually add ticker "INVALID123"
2. Generate report
3. Verify report completes without fundamentals for that ticker
4. Verify clear indicator: "Fundamentals unavailable"

### US2: Cached Fundamentals

**Test: Cache hit**
```bash
# First request
curl http://localhost:8000/api/v1/fundamentals/AAPL

# Second request (should be faster, cached: true)
curl http://localhost:8000/api/v1/fundamentals/AAPL
# Verify "cached": true in response
```

**Test: Cache expiration**
```bash
# Force refresh
curl "http://localhost:8000/api/v1/fundamentals/AAPL?refresh=true"
# Verify "cached": false and fresh data
```

**Test: Cache fallback on storage error**
1. Make SQLite file read-only (simulate corruption)
2. Request fundamentals
3. Verify data still returned (from live API)

### US3: Historical Data (P3)

**Test: Historical trends**
```bash
curl "http://localhost:8000/api/v1/fundamentals/AAPL/history?metrics=pe_ratio,revenue&periods=4"
```

Verify response includes 4 quarters of data points.

## API Quick Tests

```bash
# Single ticker
curl http://localhost:8000/api/v1/fundamentals/AAPL | jq

# Batch request
curl -X POST http://localhost:8000/api/v1/fundamentals/batch \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "MSFT", "005930.KS"]}' | jq

# Clear cache
curl -X DELETE http://localhost:8000/api/v1/fundamentals/cache \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL"]}' | jq
```

## Troubleshooting

### yfinance returns empty data
- Check ticker format (use Yahoo Finance suffix: .KS, .T, .HK)
- Verify network connectivity
- Check yfinance rate limits (2000/hour)

### investpy fails
- investing.com may be rate-limiting; check logs
- Verify investpy installed: `uv run python -c "import investpy"`

### SQLite errors
- Check file permissions on `data/fundamentals.db`
- Delete and recreate if corrupted: `rm data/fundamentals.db`

### Cache always misses
- Check system time (TTL calculation)
- Verify `expires_at` in database
