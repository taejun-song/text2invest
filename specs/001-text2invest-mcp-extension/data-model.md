# Data Model: Text2Invest

**Date**: 2026-02-11
**Source**: [spec.md](./spec.md) Key Entities section

## Core Entities

### IdeaReport

The primary output entity representing a structured investment hypothesis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (UUID) | Yes | Unique identifier |
| created_at | string (ISO 8601) | Yes | Creation timestamp |
| source | Source | Yes | Origin webpage information |
| selection_text | string | Yes | Original selected text (max 8,000 chars) |
| tickers | Ticker[] | Yes | Identified securities (may be empty) |
| thesis | string | Yes | Investment thesis statement |
| executive_summary | string[] | Yes | Max 3 bullet points |
| rationale_quotes | RationaleQuote[] | Yes | Supporting text excerpts |
| catalysts | string[] | Yes | Potential positive triggers |
| risks | string[] | Yes | Identified risk factors |
| counter_thesis | string | Yes | Opposing viewpoint |
| horizon | string | Yes | Time horizon (short/medium/long) |
| confidence_score | number | Yes | 0.0 to 1.0 |
| confidence_explanation | string | Yes | Why this confidence level |
| limitations | string[] | Yes | Known limitations of analysis |
| provider_meta | ProviderMeta | Yes | Model/provider information |

**Validation Rules**:
- `selection_text` length: 20-8000 characters
- `confidence_score`: 0.0 <= value <= 1.0
- `executive_summary`: 1-3 items
- `tickers`: 0+ items (empty valid for non-company text)

---

### Source

Origin webpage metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| url | string (URL) | Yes | Page URL |
| title | string | Yes | Page title |

---

### Ticker

Identified security with confidence.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| symbol | string | Yes | Stock ticker symbol (e.g., "AAPL") |
| company_name | string | Yes | Full company name |
| confidence | number | Yes | 0.0 to 1.0 mapping certainty |

**Validation Rules**:
- `symbol`: uppercase, 1-5 characters
- `confidence`: 0.0 <= value <= 1.0

---

### RationaleQuote

Text excerpt supporting the thesis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| quote | string | Yes | Exact text from selection |
| start_offset | integer | Yes | Character offset from start |
| end_offset | integer | Yes | Character offset to end |

**Validation Rules**:
- `start_offset` >= 0
- `end_offset` > `start_offset`
- `quote` must match selection_text[start_offset:end_offset]

---

### ProviderMeta

LLM provider information (collapsed by default in UI).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| provider | string | Yes | "openai" / "anthropic" / "ollama" |
| model | string | Yes | Model identifier |
| temperature | number | Yes | Generation temperature |
| pipeline_duration_ms | integer | Yes | Total processing time |

---

### UserSettings

User configuration stored in chrome.storage.local.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| provider | string | Yes | - | "openai" / "anthropic" / "ollama" |
| model | string | Yes | - | Model identifier |
| api_key | string | Conditional | - | Required for cloud providers |
| base_url | string | Conditional | - | Required for Ollama |
| temperature | number | No | 0.7 | Generation temperature |
| pii_redaction | boolean | No | true | Redact emails/phones |
| web_lookup | boolean | No | false | Allow web searches |

**Validation Rules**:
- `api_key` required when `provider` is "openai" or "anthropic"
- `base_url` required when `provider` is "ollama"
- `temperature`: 0.0 <= value <= 2.0

---

### Evaluation

User feedback on a report.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| idea_id | string (UUID) | Yes | Reference to IdeaReport |
| rating | string | Yes | "useful" / "not_useful" |
| notes | string | No | Optional explanation |
| created_at | string (ISO 8601) | Yes | Rating timestamp |

---

## Agent Stage Outputs

Each pipeline stage emits a validated intermediate schema.

### ExtractionOutput

| Field | Type | Description |
|-------|------|-------------|
| cleaned_text | string | Normalized text |
| language | string | Detected language code |
| word_count | integer | Token/word count |

### EntityOutput

| Field | Type | Description |
|-------|------|-------------|
| companies | string[] | Company names mentioned |
| products | string[] | Product names mentioned |
| macro_terms | string[] | Economic/macro terms |

### TickerOutput

| Field | Type | Description |
|-------|------|-------------|
| mappings | TickerMapping[] | Company-to-ticker mappings |

### TickerMapping

| Field | Type | Description |
|-------|------|-------------|
| company | string | Company name from EntityOutput |
| symbol | string | Resolved ticker symbol |
| confidence | number | Mapping confidence |
| reasoning | string | Why this mapping |

### ThesisOutput

| Field | Type | Description |
|-------|------|-------------|
| thesis | string | Investment thesis |
| supporting_quotes | RationaleQuote[] | Text evidence |
| catalysts | string[] | Positive triggers |
| horizon | string | Time horizon |

### CritiqueOutput

| Field | Type | Description |
|-------|------|-------------|
| risks | string[] | Risk factors |
| counter_thesis | string | Opposing view |
| missing_info | string[] | What's not in the text |

### ConfidenceOutput

| Field | Type | Description |
|-------|------|-------------|
| score | number | 0.0 to 1.0 |
| explanation | string | Calibration reasoning |
| limitations | string[] | Known weaknesses |

---

## State Transitions

### IdeaReport Lifecycle

```
[not_started] → [generating] → [completed]
                     ↓
                [failed]
```

### Generation States

| State | Description | UI Indication |
|-------|-------------|---------------|
| not_started | No generation in progress | Popup shows "Generate idea" |
| generating | Pipeline executing | Loading indicator, cancel button |
| completed | Report ready | "Open full report" button |
| failed | Error occurred | Error message, retry button |

---

## Storage Layout

### chrome.storage.local Keys

| Key | Type | Description |
|-----|------|-------------|
| `settings` | UserSettings | User configuration |
| `reports` | IdeaReport[] | All generated reports |
| `evaluations` | Evaluation[] | User ratings |
| `generation_state` | GenerationState | Current generation status |

### GenerationState

| Field | Type | Description |
|-------|------|-------------|
| status | string | Current state |
| request_id | string | For cancellation |
| started_at | string | Timestamp |
| current_stage | string | Active agent stage |
