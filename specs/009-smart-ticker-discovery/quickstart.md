# Quickstart: Smart Ticker Discovery

## Overview

This feature extends the TickerAgent to infer relevant companies from sector/theme analysis, even when no companies are explicitly mentioned in the text.

## Key Changes

### 1. Extended TickerOutput Model

```python
# packages/mcp-server/src/models/agent_outputs.py

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Sector(BaseModel):
    name: str
    confidence: ConfidenceLevel
    sub_sectors: list[str] = []

class InferredTicker(BaseModel):
    company_name: str
    symbol: str  # pattern: ^[A-Z0-9.\-]{1,12}$
    sector: str
    relevance_explanation: str  # max 200 chars
    confidence: ConfidenceLevel
    market_cap_tier: str  # large/mid/small
    supply_chain_layer: str | None = None
    verified: bool = True

class TickerOutput(BaseModel):
    mappings: list[TickerMapping] = []  # existing
    sectors: list[Sector] = []           # NEW
    inferred_tickers: list[InferredTicker] = []  # NEW
```

### 2. TickerAgent Changes

```python
# packages/mcp-server/src/agents/ticker.py

class TickerAgent(BaseAgent):
    async def run(self, on_thinking=None, on_retry=None, **kwargs) -> TickerOutput:
        companies = kwargs.get("companies", [])
        cleaned_text = kwargs.get("cleaned_text")  # NEW: optional text input

        # Existing: map mentioned companies to tickers
        output = await super().run(...)

        # NEW: if text provided, run sector inference
        if cleaned_text:
            inference = await self._infer_from_sectors(cleaned_text, companies)
            output.sectors = inference.sectors
            output.inferred_tickers = self._filter_and_verify(inference.inferred_tickers)

        return output

    async def _infer_from_sectors(self, text: str, existing: list[str]) -> SectorInferenceOutput:
        # Single LLM call for sector + company inference
        ...

    def _filter_and_verify(self, tickers: list[InferredTicker]) -> list[InferredTicker]:
        # 1. Filter out confidence == "low"
        # 2. Verify via yfinance, set verified=False if fails
        # 3. Deduplicate against existing mappings
        ...
```

### 3. Pipeline Integration

```python
# packages/mcp-server/src/agents/pipeline.py

# In Pipeline.run(), pass cleaned_text to TickerAgent:
ticker_output = await ticker_agent.run(
    on_thinking=...,
    companies=entity_output.companies,
    cleaned_text=extraction_output.cleaned_text,  # NEW
)
```

## Testing

```bash
cd packages/mcp-server
uv run pytest tests/test_ticker_agent.py -v
```

### Test Cases

1. **Sector inference with no companies mentioned**
   - Input: "AI chip demand is surging globally"
   - Expected: sectors=["semiconductors"], inferred_tickers includes NVDA, TSM, etc.

2. **Korean text prioritizes KOSPI**
   - Input: "반도체 수요 증가" (semiconductor demand rising)
   - Expected: 005930.KS (Samsung), 000660.KS (SK Hynix) ranked higher

3. **Deduplication with mentioned companies**
   - Input: Text mentioning Samsung + semiconductor sector
   - Expected: Samsung in mappings only, not duplicated in inferred_tickers

4. **Unverified ticker handling**
   - Mock yfinance failure
   - Expected: ticker returned with verified=False

## Example Output

```json
{
  "mappings": [
    {
      "company": "Samsung Electronics",
      "symbol": "005930.KS",
      "confidence": 0.95,
      "reasoning": "Mentioned in text [verified]"
    }
  ],
  "sectors": [
    {
      "name": "semiconductors",
      "confidence": "high",
      "sub_sectors": ["memory", "logic"]
    }
  ],
  "inferred_tickers": [
    {
      "company_name": "SK Hynix",
      "symbol": "000660.KS",
      "sector": "semiconductors",
      "relevance_explanation": "Major DRAM competitor in Korean semiconductor market",
      "confidence": "high",
      "market_cap_tier": "large",
      "supply_chain_layer": "midstream",
      "verified": true
    },
    {
      "company_name": "Micron Technology",
      "symbol": "MU",
      "sector": "semiconductors",
      "relevance_explanation": "Third-largest memory chip maker globally",
      "confidence": "high",
      "market_cap_tier": "large",
      "supply_chain_layer": "midstream",
      "verified": true
    }
  ]
}
```

## Migration Notes

- No breaking changes to existing API consumers
- `sectors` and `inferred_tickers` are optional fields with empty defaults
- Existing tests continue to pass without modification
