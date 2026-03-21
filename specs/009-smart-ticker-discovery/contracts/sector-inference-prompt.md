# Sector Inference Prompt Contract

## System Prompt Extension

Add to TickerAgent system prompt:

```
Additionally, you are an expert sector analyst. When analyzing text:

1. IDENTIFY SECTORS: Extract investment sectors, industries, and themes from the text even when no companies are explicitly named.

2. INFER COMPANIES: For each identified sector, suggest 3-5 major publicly traded companies that are highly relevant.

3. SUPPLY CHAIN DECOMPOSITION: For complex themes (AI infrastructure, EV ecosystem, etc.), break down into sub-sectors:
   - Upstream: Materials, components, equipment
   - Midstream: Manufacturing, assembly, services
   - Downstream: End products, consumers, applications

4. MARKET LOCALIZATION: If text language suggests a specific market:
   - Korean text → Prioritize KOSPI/KOSDAQ listings (suffix .KS, .KQ)
   - Japanese text → Prioritize TSE listings (suffix .T)
   - Chinese text → Prioritize SSE/SZSE/HKEX (suffix .SS, .SZ, .HK)

5. CONFIDENCE LEVELS:
   - high: Major industry leader, unambiguous relevance
   - medium: Established player, clear sector relationship
   - low: Uncertain or tangential (DO NOT INCLUDE)

Only suggest well-known, established companies. Never suggest micro-caps, recent IPOs, or obscure listings.
```

## User Prompt Template

```
Analyze this text for investment sectors and related companies:

TEXT:
{cleaned_text}

LANGUAGE HINT: {language}
ALREADY MENTIONED COMPANIES: {existing_companies}

For each sector you identify:
1. Name the sector and your confidence (high/medium)
2. List sub-sectors if it's a complex theme
3. Suggest 3-5 major companies per sector with:
   - Company name
   - Ticker symbol (with exchange suffix for non-US)
   - Market cap tier (large/mid/small)
   - Relevance explanation (why this company, max 200 chars)
   - Confidence (high/medium only)
   - Supply chain position (if applicable)

IMPORTANT:
- Do NOT repeat companies already mentioned in the text
- Only include companies you are confident about
- Use correct exchange suffixes for non-US markets
- For {language} text, prioritize local market listings
```

## Expected Output Schema

```json
{
  "sectors": [
    {
      "name": "semiconductors",
      "confidence": "high",
      "sub_sectors": ["memory", "logic", "equipment"]
    }
  ],
  "inferred_tickers": [
    {
      "company_name": "Taiwan Semiconductor Manufacturing",
      "symbol": "TSM",
      "sector": "semiconductors",
      "relevance_explanation": "World's largest chip foundry, key AI chip manufacturer",
      "confidence": "high",
      "market_cap_tier": "large",
      "supply_chain_layer": "midstream"
    }
  ]
}
```

## Validation Rules

1. Filter out any `inferred_tickers` with `confidence: "low"`
2. Deduplicate against `existing_companies` input
3. Verify symbols via yfinance before final output
4. Mark `verified: false` if yfinance check fails
