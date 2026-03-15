# Feature Specification: Multi-Agent Collaborative Investment Analysis

**Feature Branch**: `002-multi-agent-data`
**Created**: 2026-03-15
**Status**: Draft
**Input**: Enhance Text2Invest with a network of specialized agents that communicate with each other, enriching investment analysis with news data, fundamental financial data, and cross-referencing findings across data domains using the NRP.ai Qwen model.

## Overview

The current Text2Invest system produces investment ideas from user-selected text using a linear pipeline. This feature evolves the system into a multi-agent collaborative network where specialized agents each analyze a different data dimension (news, fundamentals, macro, sentiment), share findings with each other, challenge conclusions, and synthesize a comprehensive, data-backed investment report. Users gain deeper analysis grounded in real-world data beyond the selected text.

**Primary Users**: Investors, analysts, and researchers who want investment ideas supported by multiple data perspectives, not just a single text excerpt.

**Core Flow**: User triggers analysis → Existing text pipeline identifies entities/tickers → Specialized data agents launch in parallel → Agents exchange findings and cross-reference → Synthesis agent combines all perspectives → User receives enriched multi-source report with agent attribution.

## Clarifications

### Session 2026-03-15

- Q: How should agents obtain news and financial data? → A: Web search via tool calling — agents use Qwen3's tool-calling to invoke web search functions for both news and financial data. No custom API subscriptions required.
- Q: Should the system fall back to another LLM provider when NRP.ai is unavailable? → A: No fallback. NRP.ai is the sole provider for multi-agent analysis. If unavailable, display error with retry option.
- Q: Should the enriched report replace or exist alongside the original text-only report? → A: Single unified report. Enriched sections are added to the existing IdeaReport structure. One report per analysis.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data-Enriched Investment Idea (Priority: P1)

A user selects text from a news article mentioning a company. Beyond the existing text-based analysis, the system automatically researches recent news about the identified company and retrieves its key financial fundamentals. The final report includes news context, financial data points, and a thesis informed by all three sources (original text, news, fundamentals).

**Why this priority**: Core value proposition. Without multi-source enrichment, this feature delivers no incremental value over the existing text-only pipeline.

**Independent Test**: Select text mentioning a public company (e.g., Apple earnings discussion), trigger enriched analysis, verify the report contains: (1) original text-based thesis, (2) recent news references about the company, (3) fundamental data points (revenue, P/E, growth), and (4) a synthesis that references all three sources.

**Acceptance Scenarios**:

1. **Given** user selects text mentioning "Apple" and triggers enriched analysis, **When** generation completes, **Then** report includes a "News Context" section with at least 2 recent news items about Apple
2. **Given** user selects text mentioning a publicly traded company, **When** generation completes, **Then** report includes a "Fundamentals" section with key financial metrics (revenue, earnings, P/E ratio, or equivalent available data)
3. **Given** user selects text with no identifiable company, **When** generation completes, **Then** system produces a text-only report (graceful degradation) and indicates no external data was available
4. **Given** user triggers enriched analysis, **When** generation is in progress, **Then** user sees which agents are currently active and their progress

---

### User Story 2 - Agent Transparency and Attribution (Priority: P2)

After generation, the user can see which specialized agent contributed which insight. Each section of the report attributes its source (e.g., "From News Agent", "From Fundamentals Agent"), and the user can view the inter-agent communication log showing how agents shared and challenged each other's findings.

**Why this priority**: Trust requires transparency. Users must understand how the system reached its conclusions, especially when multiple data sources may conflict.

**Independent Test**: Generate an enriched report, open the agent transparency view, verify each report section shows its contributing agent, and the communication log shows at least one inter-agent message exchange.

**Acceptance Scenarios**:

1. **Given** a completed enriched report, **When** user opens the transparency view, **Then** each report section displays which agent produced it
2. **Given** agents had conflicting findings (e.g., positive news vs. declining fundamentals), **When** user views the communication log, **Then** log shows the agents' exchange where they addressed the conflict
3. **Given** a completed report, **When** user clicks on a specific insight, **Then** system shows the data source and reasoning chain that produced it

---

### User Story 3 - Inter-Agent Communication and Cross-Referencing (Priority: P3)

Agents actively communicate during analysis. The News Agent shares sentiment findings with the Fundamentals Agent, which checks whether sentiment aligns with financial reality. The Risk Agent queries both for potential red flags. This cross-referencing produces more nuanced, internally consistent reports.

**Why this priority**: Cross-referencing is what makes multi-agent superior to running agents independently. Without it, this is just parallel pipelines concatenated together.

**Independent Test**: Trigger analysis on text about a company with mixed signals (e.g., positive news but declining revenue), verify the report acknowledges the divergence and the communication log shows agents exchanging data.

**Acceptance Scenarios**:

1. **Given** news sentiment is positive but fundamentals show declining revenue, **When** agents cross-reference, **Then** the synthesis section flags the divergence with explanation
2. **Given** multiple agents identify the same risk factor, **When** cross-referencing occurs, **Then** the risk is reported once with combined evidence from both agents
3. **Given** the News Agent identifies a catalyst, **When** the Fundamentals Agent receives it, **Then** it validates the catalyst against financial data and annotates whether fundamentals support it

---

### User Story 4 - Configurable Data Sources and Agent Selection (Priority: P4)

Users can enable or disable specific data agents (News, Fundamentals, Macro) and configure which external data sources each agent may use. Users who prefer privacy can disable all external lookups and run with text-only analysis plus LLM-knowledge-based enrichment.

**Why this priority**: Extends user control and privacy. Some users may not want external API calls; others may want to customize which data sources are queried.

**Independent Test**: Disable the News Agent in settings, trigger analysis, verify the report contains no news section and the communication log shows no news agent activity.

**Acceptance Scenarios**:

1. **Given** user disables the News Agent, **When** analysis runs, **Then** report has no "News Context" section and other agents do not wait for news data
2. **Given** user disables all external data agents, **When** analysis runs, **Then** system falls back to text-only analysis with LLM general knowledge enrichment (no external API calls)
3. **Given** user enables all agents, **When** analysis runs, **Then** report includes sections from all enabled agents

---

### User Story 5 - Macro-Economic Context Agent (Priority: P5)

A specialized agent analyzes broader economic context relevant to the identified investment. It considers sector trends, interest rate environment, and economic indicators that may affect the investment thesis. This context is shared with other agents to inform their analysis.

**Why this priority**: Macro context adds depth but is not essential for a minimum viable enriched report. Valuable for sophisticated users who want broader market perspective.

**Independent Test**: Select text about a tech company, verify the report includes a "Macro Context" section referencing relevant sector trends or economic conditions, and that the thesis agent incorporated this context.

**Acceptance Scenarios**:

1. **Given** user selects text about a technology company, **When** macro agent runs, **Then** report includes relevant tech sector trends or market conditions
2. **Given** macro agent identifies a headwind (e.g., rising interest rates for growth stocks), **When** risk assessment runs, **Then** the macro headwind appears in the risk section with macro agent attribution

---

### Edge Cases

- What happens when an external data source API is unavailable? The affected agent reports "data unavailable" and other agents proceed without that data. The report clearly indicates which sections lack external data.
- What happens when agents produce contradictory conclusions? The synthesis section explicitly surfaces contradictions with evidence from each agent, rather than silently picking one.
- What happens when no tickers are identified from the text? Data agents that require tickers (Fundamentals) gracefully skip, while agents that work with broader concepts (News, Macro) still contribute if relevant keywords exist.
- What happens when the user's selected text is about a private company with no public financial data? Fundamentals Agent reports no public data available and contributes only what the LLM knows from training data, clearly marked as "LLM knowledge" rather than "live data."
- What happens when agent communication creates a circular dependency? The coordinator enforces a maximum communication depth (3 rounds) and terminates cycles, proceeding to synthesis with available data.
- What happens when enriched analysis exceeds the model's context window? The coordinator summarizes intermediate agent outputs to fit within context limits, preserving key findings and discarding verbose reasoning.
- What happens when the NRP.ai endpoint is unavailable? System displays an error message with a retry option. No fallback to other providers; multi-agent analysis requires NRP.ai.

## Requirements *(mandatory)*

### Functional Requirements

**Agent Architecture**
- **FR-001**: System MUST support at least four specialized agents: News Agent, Fundamentals Agent, Risk Agent, and Synthesis Agent
- **FR-002**: System MUST provide a Coordinator that orchestrates agent execution, manages inter-agent messaging, and enforces communication limits
- **FR-003**: Each agent MUST produce structured output with a confidence score and source attribution
- **FR-004**: Agents MUST be able to send findings to other agents and receive findings from other agents via a shared message bus
- **FR-005**: System MUST support parallel execution of independent agents (e.g., News and Fundamentals can run simultaneously)
- **FR-006**: System MUST enforce a maximum of 3 communication rounds between agents to prevent infinite loops

**News Analysis**
- **FR-007**: The News Agent MUST search for recent news items about identified companies or topics via LLM tool-calling with web search functions
- **FR-008**: The News Agent MUST extract sentiment (positive, negative, neutral) from each news item
- **FR-009**: The News Agent MUST produce a structured summary with news items, sentiment, and relevance scores

**Fundamentals Analysis**
- **FR-010**: The Fundamentals Agent MUST retrieve key financial metrics for identified public companies via LLM tool-calling with web search functions when available
- **FR-011**: Financial metrics MUST include at minimum: revenue, earnings, P/E ratio, and revenue growth rate (when available)
- **FR-012**: The Fundamentals Agent MUST clearly distinguish between live data and LLM-knowledge-based estimates

**Cross-Referencing**
- **FR-013**: System MUST cross-reference news sentiment against fundamental data trends to identify convergences and divergences
- **FR-014**: System MUST deduplicate findings when multiple agents identify the same insight
- **FR-015**: System MUST surface contradictions between agents' conclusions rather than silently resolving them

**Synthesis and Output**
- **FR-016**: The Synthesis Agent MUST produce an enriched investment report combining all agent findings
- **FR-017**: Each section of the enriched report MUST attribute its source agent(s)
- **FR-018**: The single unified report MUST include all sections from the original IdeaReport plus optional enrichment sections (News Context, Fundamentals Summary, Cross-Reference Analysis, Macro Context) present only when their corresponding agents are enabled and produce results
- **FR-019**: System MUST support graceful degradation to text-only analysis when data agents are disabled or fail

**Communication Log**
- **FR-020**: System MUST record all inter-agent messages with timestamps, sender, recipient, and content
- **FR-021**: Users MUST be able to view the inter-agent communication log for any completed report
- **FR-022**: Communication log MUST be stored locally alongside the report

**Configuration**
- **FR-023**: Users MUST be able to enable or disable individual data agents
- **FR-024**: System MUST support NRP.ai as a provider with OpenAI-compatible endpoint configuration
- **FR-025**: System MUST default to text-only analysis when no external data agents are enabled
- **FR-026**: Users MUST be able to configure whether agents use external data lookups or rely solely on LLM knowledge

**Privacy and Data Handling**
- **FR-027**: System MUST NOT send user-selected text to external data APIs; only derived identifiers (company names, ticker symbols) are used for external lookups
- **FR-028**: System MUST clearly indicate in the report which data came from external sources vs. LLM knowledge
- **FR-029**: All external data lookups MUST respect the existing web lookup toggle (default OFF)

### Key Entities

- **AgentMessage**: A message exchanged between agents during collaborative analysis. Contains sender agent ID, recipient agent ID, message type (finding, query, challenge, response), structured content, timestamp, and round number.

- **EnrichedReport**: Single unified report that extends the existing IdeaReport with additional optional sections: News Context, Fundamentals Summary, Cross-Reference Analysis, Macro Context, agent attribution per section, and a reference to the communication log. When data agents are disabled or produce no results, those sections are simply absent. One report per analysis — no separate text-only and enriched reports.

- **NewsItem**: A news reference discovered by the News Agent. Contains headline, source, publication date, sentiment (positive/negative/neutral), relevance score (0-1), and summary.

- **FundamentalsSnapshot**: Financial data for a company at analysis time. Contains ticker, metrics (key-value pairs of metric name to value), data source indicator (live/LLM-knowledge), and retrieval timestamp.

- **AgentConfig**: Per-agent configuration including enabled status, data source preferences, and maximum response time.

- **CommunicationLog**: Ordered collection of AgentMessages for a single analysis session. Contains session ID, all messages, total rounds used, and wall-clock duration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Enriched reports contain data from at least 2 sources (text + news or text + fundamentals) for 80% of analyses involving publicly traded companies
- **SC-002**: Users can identify which agent produced each insight within 5 seconds of viewing the report
- **SC-003**: Cross-reference analysis correctly identifies sentiment-vs-fundamentals divergence in 90% of cases where such divergence exists
- **SC-004**: Enriched analysis completes within 60 seconds for standard analyses (text under 2,000 characters, up to 3 tickers)
- **SC-005**: System gracefully degrades to text-only analysis within 5 seconds when all data agents are disabled or unavailable
- **SC-006**: Inter-agent communication log is available for 100% of enriched reports
- **SC-007**: Users can configure agent selection and data source preferences in under 30 seconds

## Assumptions

- The NRP.ai managed LLM service (base URL: `https://ellm.nrp-nautilus.io/v1`) is available and the Qwen model (`qwen3`) is the primary model used for all agents
- The NRP.ai endpoint is OpenAI-compatible and works with the existing LiteLLM provider abstraction
- The provided API token grants sufficient access for multi-agent workloads
- NRP.ai is the sole LLM provider for multi-agent analysis with no fallback; availability depends on the NRP.ai service
- All external data (news and financial) is sourced via Qwen3's tool-calling capability with web search functions; no custom API subscriptions are required
- When external lookups are disabled, agents fall back to LLM training knowledge only
- The Qwen3 model supports tool/function calling, enabling agents to fetch external data
- The existing Text2Invest text analysis pipeline (feature 001) is complete and available as a foundation
- English-language analysis only (consistent with feature 001)
- All agent communication happens server-side; the extension displays results

## Known Limitations

- Agent quality depends heavily on the LLM's ability to use tools effectively and produce structured outputs
- Real-time market data is not in scope; fundamentals data reflects what is available via configured tools or LLM knowledge
- The number of communication rounds (max 3) is a pragmatic limit; complex analyses may benefit from more rounds in future iterations
- External data source availability and rate limits may affect report completeness
- Multi-agent analysis increases latency compared to the existing linear pipeline
