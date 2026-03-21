# Data Model: Smart Ticker Discovery

**Feature**: 009-smart-ticker-discovery
**Date**: 2026-03-21

## Entity Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  TickerOutput   │────▶│  TickerMapping   │     │ InferredTicker  │
│  (extended)     │     │  (existing)      │     │ (new)           │
└────────┬────────┘     └──────────────────┘     └────────┬────────┘
         │                                                 │
         │ inferred_tickers                               │
         └─────────────────────────────────────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │     Sector      │
                     │     (new)       │
                     └─────────────────┘
```

## Entities

### ConfidenceLevel (Enum)

Qualitative confidence for inferred tickers.

| Value | Description |
|-------|-------------|
| `high` | Well-known major company, very high certainty |
| `medium` | Established company, reasonable certainty |
| `low` | Uncertain, should be filtered out |

```python
class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```

### Sector

An industry or market segment identified from text.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | str | required, min 1 char | Sector name (e.g., "semiconductors") |
| `confidence` | ConfidenceLevel | required | How confident in sector identification |
| `sub_sectors` | list[str] | optional | Supply chain layers or sub-industries |

```python
class Sector(BaseModel):
    name: str = Field(..., min_length=1)
    confidence: ConfidenceLevel
    sub_sectors: list[str] = Field(default_factory=list)
```

### InferredTicker

A company not mentioned in text but relevant to an identified sector.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `company_name` | str | required | Full company name |
| `symbol` | str | pattern `^[A-Z0-9.\-]{1,12}$` | Ticker symbol with exchange suffix |
| `sector` | str | required | Which sector this company belongs to |
| `relevance_explanation` | str | required, max 200 chars | Why this company was inferred |
| `confidence` | ConfidenceLevel | required | Confidence in this inference |
| `market_cap_tier` | str | one of: large/mid/small | Company size category |
| `supply_chain_layer` | str | optional | Position in value chain |
| `verified` | bool | default True | Whether yfinance verification succeeded |

```python
class InferredTicker(BaseModel):
    company_name: str = Field(...)
    symbol: str = Field(..., pattern=r"^[A-Z0-9.\-]{1,12}$")
    sector: str = Field(...)
    relevance_explanation: str = Field(..., max_length=200)
    confidence: ConfidenceLevel
    market_cap_tier: str = Field(..., pattern=r"^(large|mid|small)$")
    supply_chain_layer: str | None = None
    verified: bool = True
```

### TickerOutput (Extended)

Extended to include inferred tickers alongside existing mappings.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `mappings` | list[TickerMapping] | existing | Direct company-to-ticker mappings |
| `sectors` | list[Sector] | new, optional | Identified sectors from text |
| `inferred_tickers` | list[InferredTicker] | new, optional | Sector-inferred companies |

```python
class TickerOutput(BaseModel):
    mappings: list[TickerMapping] = Field(default_factory=list)
    sectors: list[Sector] = Field(default_factory=list)
    inferred_tickers: list[InferredTicker] = Field(default_factory=list)
```

### SectorInferenceInput

Input model for sector inference (internal use).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `cleaned_text` | str | required | Text to analyze for sectors |
| `language` | str | optional | Detected language code |
| `existing_companies` | list[str] | optional | Already-mentioned companies |

## Relationships

```
TickerOutput
├── mappings: list[TickerMapping]    # 1:N - existing
├── sectors: list[Sector]             # 1:N - identified sectors
└── inferred_tickers: list[InferredTicker]  # 1:N - per-sector companies
    └── sector: str                   # References Sector.name
```

## Validation Rules

1. **InferredTicker.confidence**: Only `high` or `medium` values should be returned in final output (FR-010)
2. **InferredTicker.symbol**: Must match exchange-suffixed pattern for non-US markets (FR-004)
3. **Deduplication**: If a ticker appears in both `mappings` and `inferred_tickers`, keep only in `mappings` with merged reasoning (FR-009)
4. **Minimum coverage**: At least 3 inferred tickers per sector when major companies exist (FR-003)

## State Transitions

```
Text Input
    │
    ▼
┌────────────────────┐
│ SECTOR_IDENTIFIED  │ ── sectors extracted from text
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ TICKERS_INFERRED   │ ── companies inferred per sector
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ VERIFICATION       │ ── yfinance verification attempted
│ (verified/unverified)
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ FILTERED           │ ── low confidence removed
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ DEDUPLICATED       │ ── merged with direct mappings
└────────────────────┘
```

## Migration Notes

- `TickerOutput.sectors` and `TickerOutput.inferred_tickers` are optional with empty list defaults
- Existing consumers that only use `mappings` field continue to work unchanged
- New fields are additive, no breaking changes to existing serialization
