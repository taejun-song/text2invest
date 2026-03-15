# Feature Specification: Ticker Recommendation & Expanded Search

**Feature Branch**: `006-ticker-recommendation`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "I want this agent to find a related ticker continuously expanding the search, and explicitly recommend buy/sell with certainty of percentage"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Explicit Buy/Sell Recommendation (Priority: P1)

A user selects text about a company or investment topic. After the report generates, each identified ticker displays an explicit recommendation — BUY, SELL, or HOLD — with a certainty percentage and a brief rationale. This replaces the current ambiguous confidence score with an actionable trading directive.

**Why this priority**: The core value proposition. Without explicit recommendations, users must interpret thesis text and confidence scores themselves. An explicit BUY/SELL/HOLD signal with certainty dramatically reduces the cognitive burden and makes the tool immediately actionable.

**Independent Test**: Select text mentioning a publicly traded company, generate a report, and verify each ticker in the report shows a recommendation (BUY/SELL/HOLD), a certainty percentage (0-100%), and a one-sentence rationale.

**Acceptance Scenarios**:

1. **Given** a user selects text about a company with positive catalysts and strong fundamentals, **When** the report generates, **Then** each ticker shows a recommendation (e.g., "BUY — 78% certainty") with a rationale explaining the signal.
2. **Given** a user selects text about a company facing significant headwinds, **When** the report generates, **Then** the ticker shows a SELL or HOLD recommendation with appropriate certainty and rationale.
3. **Given** the analysis produces mixed signals (strong thesis but high risks), **When** the report generates, **Then** the ticker shows a HOLD recommendation with moderate certainty and a rationale noting the conflicting signals.
4. **Given** the system has insufficient data to form a recommendation, **When** the report generates, **Then** the ticker shows HOLD with low certainty and a rationale stating insufficient data.

---

### User Story 2 - Related Ticker Discovery (Priority: P2)

After identifying the primary ticker(s) from the selected text, the system automatically discovers related companies — competitors, supply chain partners, sector peers, and companies affected by the same catalysts. Each related ticker also receives a recommendation. This expands a single text selection into a broader investment perspective.

**Why this priority**: Expands the tool's value from single-stock analysis to sector-aware discovery. Users often want to compare alternatives or understand the competitive landscape, but manually researching related companies is time-consuming.

**Independent Test**: Select text about Apple (AAPL), generate a report, and verify the report includes related tickers (e.g., MSFT, GOOGL as competitors; TSM as supply chain) beyond those directly mentioned in the text, each with their own recommendation.

**Acceptance Scenarios**:

1. **Given** a user selects text mentioning Tesla, **When** the report generates, **Then** the report includes related tickers such as competitors (e.g., RIVN, GM), supply chain (e.g., PANW for batteries), or sector peers, clearly labeled as "related" with a relationship description.
2. **Given** a user selects text mentioning a niche company with few public peers, **When** the report generates, **Then** the system identifies at least the sector and any available peers, or explicitly states limited related tickers found.
3. **Given** the system discovers related tickers, **When** displayed in the report, **Then** each related ticker shows: symbol, company name, relationship type (competitor, supplier, peer), recommendation, and certainty percentage.

---

### User Story 3 - Expanding Search Depth Control (Priority: P3)

Users can control how broadly the system searches for related tickers through a setting. A "search depth" control lets users choose between focused analysis (primary tickers only) and expansive discovery (up to 2 levels of related companies). The default searches one level of related companies.

**Why this priority**: Power users want control over breadth vs. speed. A deeper search yields more tickers but takes longer to generate. This gives users agency over the trade-off.

**Independent Test**: In settings, set search depth to "Focused" (no expansion), generate a report, and verify only directly mentioned tickers appear. Change to "Expanded" (2 levels), regenerate, and verify additional related tickers appear.

**Acceptance Scenarios**:

1. **Given** a user sets search depth to "Focused", **When** the report generates, **Then** only tickers directly mentioned in or inferred from the selected text appear — no related ticker expansion.
2. **Given** a user sets search depth to "Standard" (default), **When** the report generates, **Then** the report includes the primary tickers plus one level of directly related companies.
3. **Given** a user sets search depth to "Expanded", **When** the report generates, **Then** the report includes primary tickers, first-level related companies, and second-level connections (related to related), clearly labeled by depth level.

---

### Edge Cases

- What happens when no tickers can be identified from the selected text? The system generates a report without recommendations and displays a message stating no investable tickers were identified.
- What happens when a related ticker search returns too many results (e.g., 50+ related companies)? The system caps related tickers at 10 per primary ticker, prioritized by relevance and market significance.
- What happens when the selected text discusses a private company? The system notes the company is private (not publicly traded) and attempts to find publicly traded competitors or parent companies instead.
- What happens when conflicting signals exist across data sources (news positive, fundamentals negative)? The recommendation reflects the aggregate view with certainty adjusted downward, and the rationale explicitly notes the conflicting signals.
- What happens when a related ticker is in a different market/exchange (e.g., foreign stocks)? The system includes tickers from major global exchanges but labels the exchange (e.g., "7203.T — Toyota Motor, TSE").

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a recommendation of BUY, SELL, or HOLD for each identified ticker in the report.
- **FR-002**: Each recommendation MUST include a certainty percentage between 0% and 100%.
- **FR-003**: Each recommendation MUST include a one-sentence rationale explaining the signal.
- **FR-004**: The recommendation MUST be derived from the aggregate analysis — thesis strength, risk severity, confidence score, catalyst quality, fundamentals data (if available), and news sentiment (if available).
- **FR-005**: System MUST discover related tickers by identifying competitors, supply chain partners, and sector peers of each primary ticker.
- **FR-006**: Related tickers MUST be labeled with a relationship type (competitor, supplier, customer, sector peer, parent/subsidiary).
- **FR-007**: Each related ticker MUST also receive a recommendation (BUY/SELL/HOLD) with certainty and rationale.
- **FR-008**: The report display MUST visually distinguish primary tickers (directly from text) from related/discovered tickers.
- **FR-009**: Users MUST be able to select a search depth (Focused / Standard / Expanded) in settings.
- **FR-010**: The search depth setting MUST default to "Standard" (one level of related tickers).
- **FR-011**: System MUST cap related tickers at 10 per primary ticker to prevent unbounded expansion.
- **FR-012**: System MUST include a disclaimer that recommendations are AI-generated analysis, not professional financial advice.
- **FR-013**: The recommendation certainty MUST decrease when conflicting signals are detected across data sources.
- **FR-014**: Private companies MUST be identified as non-tradeable, with the system suggesting publicly traded alternatives when available.

### Key Entities

- **Recommendation**: An actionable signal (BUY/SELL/HOLD) associated with a ticker, including certainty percentage (0-100), rationale text, and the signal factors that contributed to the recommendation.
- **RelatedTicker**: A discovered ticker not directly mentioned in the source text, including the relationship type to the primary ticker, the discovery depth level (1 or 2), and its own recommendation.
- **SearchDepth**: A user preference controlling the breadth of related ticker discovery — Focused (0 levels), Standard (1 level, default), or Expanded (2 levels).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every report with at least one identified ticker includes a BUY/SELL/HOLD recommendation with certainty percentage for each ticker.
- **SC-002**: When search depth is set to Standard or Expanded, at least 2 related tickers are discovered for each primary ticker that represents a well-known public company.
- **SC-003**: Users can distinguish between primary and related tickers at a glance within the report.
- **SC-004**: Report generation with Standard search depth completes within 2x the current generation time.
- **SC-005**: The recommendation certainty correlates with data availability — tickers with more data sources (news + fundamentals + macro) show higher certainty than those analyzed from text alone.
- **SC-006**: 80% of users find the explicit recommendation more actionable than the previous confidence-score-only format.
- **SC-007**: Related ticker discovery surfaces at least 1 competitor or sector peer that the user did not initially consider.

## Assumptions

- Recommendations are based solely on the LLM's analysis of available context (selected text, news, fundamentals, macro data). They are not connected to real-time trading systems or professional analyst ratings.
- The system does not track recommendation accuracy over time in this version. Backtesting or performance tracking may be added in a future feature.
- Related ticker discovery relies on the LLM's knowledge of company relationships. When web search is enabled for data agents, more accurate peer/competitor identification is expected.
- The system supports tickers from major global exchanges (NYSE, NASDAQ, LSE, TSE, etc.) but does not guarantee coverage of all markets.
- The existing disclaimer ("Educational only — Not financial advice") remains and is reinforced alongside recommendations.
