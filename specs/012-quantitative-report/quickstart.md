# Quickstart: Quantitative Investment Report

## Prerequisites

- MCP server running (`uv run uvicorn api_server:app --host 0.0.0.0 --port 8000`)
- Existing fundamentals infrastructure from spec 011

## Validation Scenarios

### Scenario 1: Technical Indicators Endpoint

**Test**: Verify technical indicators are calculated correctly

```bash
# Get technical indicators for AAPL
curl http://localhost:8000/api/v1/technicals/AAPL | jq

# Expected: Response includes ma_50, ma_200, rsi_14, price changes
```

**Success criteria**:
- RSI value between 0-100
- MA50 and MA200 are reasonable prices
- Price changes are percentages (decimals)

### Scenario 2: Combined Quantitative Report

**Test**: Verify combined endpoint returns all data types

```bash
# Get full quantitative report
curl http://localhost:8000/api/v1/quantitative/AAPL | jq

# Expected: fundamentals, technicals, and valuation sections
```

**Success criteria**:
- Fundamentals include P/E, market cap, EPS
- Technicals include moving averages, RSI
- Valuation includes sector comparison

### Scenario 3: Confidence Score Removed

**Test**: Verify confidence_score no longer appears in reports

```bash
# Generate a report via the extension or API
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{
    "selection_text": "Apple reported strong iPhone sales growth...",
    "url": "https://example.com",
    "title": "Test",
    "user_settings": {
      "provider": "nrp",
      "model": "deepseek/deepseek-chat-v3-0324",
      "api_key": "YOUR_KEY",
      "base_url": "https://api.nrp.ai/v1"
    }
  }' | jq '.confidence_score, .quantitative_data'

# Expected: confidence_score is null, quantitative_data has values
```

**Success criteria**:
- `confidence_score` is null or absent
- `quantitative_data` array contains metrics

### Scenario 4: Missing Data Handling

**Test**: Verify graceful handling of unavailable data

```bash
# Test with a ticker that may have missing data
curl http://localhost:8000/api/v1/technicals/INVALID123 | jq

# Expected: Error response or partial data with nulls
```

**Success criteria**:
- No server crash
- Clear error message or null values for missing fields

### Scenario 5: International Ticker

**Test**: Verify international tickers work

```bash
# Test Samsung (Korean market)
curl http://localhost:8000/api/v1/quantitative/005930.KS | jq

# Expected: Data returned with KRW currency
```

**Success criteria**:
- Data retrieved successfully
- Currency displayed correctly

## Manual UI Validation

1. Open Chrome extension sidepanel
2. Select text about a company on any webpage
3. Click "Generate Report"
4. Verify:
   - Quantitative metrics section appears
   - No "Confidence Score" section visible
   - Technical indicators (MA, RSI) displayed
   - Fundamental metrics (P/E, Market Cap) displayed

## Performance Check

```bash
# Time a full report generation
time curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"selection_text": "...", ...}'

# Expected: Under 10 seconds total
```
