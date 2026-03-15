# Data Model: Multi-Agent Collaborative Investment Analysis

**Date**: 2026-03-15
**Source**: [spec.md](./spec.md) Key Entities section

## Extended Core Entities

### IdeaReport (Extended)

The existing IdeaReport is extended with optional enrichment fields. All existing fields are preserved unchanged.

**New Optional Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| news_context | NewsItem[] | No | News items discovered by the News Agent |
| fundamentals_summary | FundamentalsSnapshot[] | No | Financial data per ticker from the Fundamentals Agent |
| cross_reference_analysis | CrossReferenceAnalysis | No | Convergences and divergences between agents |
| macro_context | MacroContext | No | Macro-economic context from the Macro Agent |
| agent_attributions | dict[string, string[]] | No | Map of report section name → contributing agent IDs |
| communication_log | CommunicationLog | No | Full inter-agent communication record |

**Behavior**: When data agents are disabled or produce no results, enrichment fields are `None`. The report remains valid as a standard IdeaReport.

---

## New Entities

### NewsItem

A news reference discovered by the News Agent via web search.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| headline | string | Yes | News article headline |
| source | string | Yes | Publication or website name |
| url | string (URL) | Yes | Link to the article |
| published_date | string | Yes | Publication date (ISO 8601 or human-readable) |
| sentiment | string | Yes | "positive" / "negative" / "neutral" |
| relevance_score | number | Yes | 0.0 to 1.0 relevance to the investment thesis |
| summary | string | Yes | 2-3 sentence summary of the article |
| data_source | string | Yes | "web_search" / "llm_knowledge" |

**Validation Rules**:
- `relevance_score`: 0.0 <= value <= 1.0
- `sentiment`: must be one of positive, negative, neutral

---

### FundamentalsSnapshot

Financial data for a company at analysis time.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ticker | string | Yes | Stock ticker symbol |
| company_name | string | Yes | Full company name |
| metrics | FinancialMetric[] | Yes | Key financial metrics |
| data_source | string | Yes | "web_search" / "llm_knowledge" |
| retrieved_at | string (ISO 8601) | Yes | When data was retrieved |

---

### FinancialMetric

A single financial metric value.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Metric name (e.g., "Revenue", "P/E Ratio") |
| value | string | Yes | Metric value as formatted string (e.g., "$394.3B", "28.5x") |
| period | string | No | Reporting period (e.g., "FY2025", "Q3 2025") |

---

### CrossReferenceAnalysis

Cross-agent comparison results.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| convergences | string[] | Yes | Findings where multiple agents agree |
| divergences | Divergence[] | Yes | Findings where agents disagree |
| deduplicated_risks | string[] | Yes | Risks identified by multiple agents, reported once |

---

### Divergence

A specific disagreement between agents.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| topic | string | Yes | What the divergence is about |
| finding_a | string | Yes | First agent's conclusion |
| source_a | string | Yes | Agent ID that produced finding_a |
| finding_b | string | Yes | Second agent's conclusion |
| source_b | string | Yes | Agent ID that produced finding_b |
| explanation | string | Yes | Synthesis Agent's analysis of the divergence |

---

### MacroContext

Macro-economic context analysis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sector | string | Yes | Relevant sector/industry |
| sector_trends | string[] | Yes | Current sector-level trends |
| economic_indicators | string[] | Yes | Relevant economic indicators |
| headwinds | string[] | Yes | Negative macro factors |
| tailwinds | string[] | Yes | Positive macro factors |
| data_source | string | Yes | "web_search" / "llm_knowledge" |

---

### AgentMessage

A message exchanged between agents during collaborative analysis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (UUID) | Yes | Unique message identifier |
| sender | string | Yes | Sending agent ID (e.g., "news_agent") |
| recipient | string | Yes | Receiving agent ID or "broadcast" for all |
| message_type | string | Yes | "finding" / "query" / "challenge" / "response" |
| content | object | Yes | Structured message payload |
| timestamp | string (ISO 8601) | Yes | When message was sent |
| round_number | integer | Yes | Communication round (1-3) |

**Validation Rules**:
- `round_number`: 1 <= value <= 3
- `message_type`: must be one of finding, query, challenge, response

---

### CommunicationLog

Complete record of inter-agent communication for one analysis session.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (UUID) | Yes | Unique log identifier |
| messages | AgentMessage[] | Yes | All messages in chronological order |
| total_rounds | integer | Yes | Number of communication rounds used |
| duration_ms | integer | Yes | Total wall-clock time for agent collaboration |

---

### AgentConfig

Per-agent configuration stored as part of user settings.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| agent_id | string | Yes | - | Agent identifier (e.g., "news_agent") |
| enabled | boolean | Yes | true | Whether agent participates in analysis |
| use_external_data | boolean | Yes | true | Whether agent can make web searches |

---

### UserSettings (Extended)

Additional fields for multi-agent configuration.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| agent_configs | AgentConfig[] | No | all enabled | Per-agent settings |

**Note**: NRP.ai is configured using the existing provider/model/api_key/base_url fields with provider set to "nrp".

---

## Agent Output Models (Pipeline Intermediaries)

### NewsAgentOutput

| Field | Type | Description |
|-------|------|-------------|
| news_items | NewsItem[] | Discovered news articles |
| overall_sentiment | string | Aggregate sentiment across all news |
| key_themes | string[] | Recurring themes in news coverage |
| confidence_score | number (0.0-1.0) | Agent's confidence in the quality and completeness of its findings |

### FundamentalsAgentOutput

| Field | Type | Description |
|-------|------|-------------|
| snapshots | FundamentalsSnapshot[] | Financial data per ticker |
| assessment | string | Summary assessment of financial health |
| confidence_score | number (0.0-1.0) | Agent's confidence in the quality and completeness of its findings |

### RiskAgentOutput

| Field | Type | Description |
|-------|------|-------------|
| risks | string[] | Identified risk factors from all sources |
| risk_sources | dict[string, string[]] | Map of risk → source agent IDs |
| severity_ranking | string[] | Risks ordered by severity |
| confidence_score | number (0.0-1.0) | Agent's confidence in the quality and completeness of its findings |

### MacroAgentOutput

| Field | Type | Description |
|-------|------|-------------|
| context | MacroContext | Macro-economic analysis |
| impact_assessment | string | How macro factors affect the investment thesis |
| confidence_score | number (0.0-1.0) | Agent's confidence in the quality and completeness of its findings |

### SynthesisAgentOutput

| Field | Type | Description |
|-------|------|-------------|
| enriched_thesis | string | Thesis revised with all agent inputs |
| enriched_executive_summary | string[] | Updated executive summary (max 3 bullets) |
| cross_reference | CrossReferenceAnalysis | Cross-agent comparison |
| agent_attributions | dict[string, string[]] | Section → agent attribution |

---

## Storage Layout

### chrome.storage.local Keys (Extended)

| Key | Type | Description |
|-----|------|-------------|
| `settings` | UserSettings | User configuration (extended with agent_configs) |
| `reports` | IdeaReport[] | All generated reports (now includes enrichment fields) |

**Note**: Communication logs are stored inline within each report's `communication_log` field. No separate storage key needed.

---

## Provider Enum Extension

| Value | Description |
|-------|-------------|
| "openai" | OpenAI API (existing) |
| "anthropic" | Anthropic API (existing) |
| "ollama" | Ollama local (existing) |
| "nrp" | NRP.ai managed LLM service (new) |
