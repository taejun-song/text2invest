# Feature Specification: Smart Ticker Discovery

**Feature Branch**: `009-smart-ticker-discovery`
**Created**: 2026-03-19
**Status**: Draft
**Input**: User description: "I want you to try hard to get the ticker, not just directly from the text, but extend your thoughts. For example, the given text is related with semiconductor, then you may come up with micron or samsung electronics, sk hynix, etc. Find the sector and be more like human experts to find the related tickers."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sector-Aware Ticker Inference (Priority: P1)

A user selects text discussing an industry trend (e.g., "global semiconductor demand is surging due to AI workloads") without naming specific companies. The system identifies the sector (semiconductors), then infers and returns the most relevant publicly traded companies in that sector — just like a human analyst would.

**Why this priority**: This is the core value proposition. Currently, the system only finds tickers for companies explicitly named in the text. Most investment-relevant articles discuss trends, sectors, and themes without listing every relevant company. An expert analyst reading about "semiconductor demand" immediately thinks Samsung, Micron, TSMC, SK Hynix — the system should do the same.

**Independent Test**: Select text about "AI chip demand" with no company names. System should return at least 3 relevant semiconductor companies with tickers.

**Acceptance Scenarios**:

1. **Given** text about rising semiconductor demand with no company names, **When** analyzed, **Then** the system identifies the semiconductor sector and returns at least 3 major companies (e.g., TSMC, Samsung Electronics, Micron) with their correct ticker symbols
2. **Given** text mentioning "EV battery supply chain bottlenecks", **When** analyzed, **Then** the system infers battery/EV sector and returns relevant companies (e.g., CATL, LG Energy Solution, Panasonic)
3. **Given** text that already mentions Samsung Electronics explicitly, **When** analyzed, **Then** the system still infers additional sector peers (e.g., SK Hynix, Micron, TSMC) beyond just the named company

---

### User Story 2 - Expert-Level Sector Decomposition (Priority: P2)

When text covers a complex supply chain or multi-sector theme, the system decomposes it into sub-sectors and identifies key players across each layer — upstream (materials/equipment), midstream (manufacturing), and downstream (end products/consumers).

**Why this priority**: Real investment analysis considers the full value chain. An expert reading about "AI infrastructure buildout" thinks beyond chip makers to include cloud providers, data center REITs, networking equipment, and power suppliers.

**Independent Test**: Select text about "AI infrastructure spending" and verify the system returns companies across multiple supply chain layers (chips, cloud, networking, power).

**Acceptance Scenarios**:

1. **Given** text about "AI infrastructure buildout", **When** analyzed, **Then** results include companies from at least 2 distinct supply chain layers (e.g., chip makers AND cloud providers)
2. **Given** text about "renewable energy transition", **When** analyzed, **Then** results span solar, wind, battery storage, and grid infrastructure companies
3. **Given** text about a niche sector with few public companies, **When** analyzed, **Then** the system returns what is available and indicates limited coverage rather than forcing irrelevant matches

---

### User Story 3 - Market-Localized Expert Knowledge (Priority: P2)

When text is in a specific language or references a specific market, the system applies region-appropriate expert knowledge. A Korean-language text about semiconductors should prioritize Korean-listed companies (Samsung, SK Hynix on KOSPI) alongside global peers, not just US listings.

**Why this priority**: Investment analysis is market-context-dependent. A Korean investor reading Korean text about semiconductors cares most about KOSPI-listed companies, while still wanting global context.

**Independent Test**: Select Korean-language text about semiconductors and verify Korean-listed tickers appear first, with global peers also included.

**Acceptance Scenarios**:

1. **Given** Korean text about semiconductor trends, **When** analyzed, **Then** Korean-listed companies (e.g., 005930.KS, 000660.KS) appear with higher relevance than US-only equivalents
2. **Given** Japanese text about automotive industry, **When** analyzed, **Then** TSE-listed companies (e.g., Toyota 7203.T, Honda 7267.T) are prioritized alongside global peers
3. **Given** English text with no geographic bias, **When** analyzed, **Then** the system returns globally diversified results across major exchanges

---

### User Story 4 - Confidence-Weighted Inferred Tickers (Priority: P3)

Inferred tickers (not explicitly mentioned in text) are clearly distinguished from directly mentioned tickers. Each inferred ticker includes a relevance explanation so the user understands why the system suggested it.

**Why this priority**: Users need to trust the system's inference. Mixing inferred companies with explicitly mentioned ones without distinction would be confusing and reduce trust.

**Independent Test**: Generate a report from text mentioning one company in a sector. Verify that explicitly mentioned tickers are labeled differently from inferred sector peers, and each inferred ticker has a relevance explanation.

**Acceptance Scenarios**:

1. **Given** text mentioning only "Samsung Electronics" in a semiconductor context, **When** analyzed, **Then** the report shows Samsung as "directly mentioned" and Micron/TSMC/SK Hynix as "inferred from sector"
2. **Given** inferred tickers in the report, **When** the user reviews them, **Then** each inferred ticker has a human-readable explanation (e.g., "Major DRAM competitor in the same semiconductor memory market")

---

### Edge Cases

- What happens when the text is too vague to identify any sector (e.g., "the market went up today")? System returns no inferred tickers and proceeds with explicitly mentioned companies only.
- What happens when the inferred sector has no publicly traded pure-play companies? System notes limited coverage and returns the closest available public companies.
- What happens when text discusses multiple unrelated sectors? System identifies each sector independently and returns relevant companies for each.
- What happens when inferred companies overlap with the existing Discovery Agent's related companies? Deduplicate: if the same ticker appears from both inference and discovery, keep the higher-confidence entry and merge reasoning.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST analyze the selected text to identify sectors, industries, and investment themes beyond just explicit company names
- **FR-002**: System MUST infer relevant publicly traded companies for each identified sector/theme, even when no companies are mentioned in the text
- **FR-003**: System MUST return at least 3 inferred companies per identified sector when major public companies exist in that sector
- **FR-004**: Inferred companies MUST include the correct ticker symbol with appropriate exchange suffix for non-US markets
- **FR-005**: Each inferred company MUST include a relevance explanation describing why it was suggested (e.g., sector relationship, market position)
- **FR-006**: Inferred tickers MUST be clearly distinguished from directly mentioned tickers in the output, with a source label (e.g., "mentioned" vs "inferred")
- **FR-007**: System MUST consider the text's language and geographic context when prioritizing inferred companies (e.g., Korean text should prioritize KOSPI-listed companies)
- **FR-008**: System MUST decompose complex themes into sub-sectors when applicable (e.g., "AI infrastructure" → chips, cloud, networking, power)
- **FR-009**: System MUST deduplicate tickers that appear from both direct mention and sector inference, keeping the entry with higher confidence
- **FR-010**: System MUST NOT return inferred tickers with "low" confidence — only include tickers rated "high" or "medium" confidence by LLM judgment (well-known, established companies in the identified sector)
- **FR-011**: System MUST handle text with no identifiable sector gracefully, returning no inferred tickers rather than forcing irrelevant matches
- **FR-012**: Inferred ticker discovery MUST NOT significantly increase total analysis time — the additional inference should complete within the existing pipeline flow
- **FR-013**: When ticker validation fails (yfinance unavailable, rate limited, or ticker not found), the system MUST still return inferred tickers with a "verified: false" flag rather than excluding them

### Key Entities

- **Sector**: An industry or market segment identified from the text (e.g., "semiconductors", "renewable energy"). Has attributes: name, confidence, sub-sectors
- **Inferred Company**: A company not mentioned in the text but relevant to an identified sector. Has attributes: company name, ticker symbol, sector, relevance explanation, confidence (high/medium/low), source ("inferred"), market cap tier, verified (boolean)
- **Supply Chain Layer**: A position within a sector's value chain (e.g., upstream materials, midstream manufacturing, downstream products). Used for expert-level decomposition

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For text discussing a recognizable sector without naming companies, the system returns at least 3 relevant inferred tickers in 80% of cases
- **SC-002**: 90% of inferred tickers are real, publicly traded companies on the correct exchange (verified by market data)
- **SC-003**: Users can distinguish inferred tickers from mentioned tickers at a glance in the report
- **SC-004**: Total analysis time increases by no more than 30% compared to the current pipeline
- **SC-005**: For Korean/Japanese/Chinese text, at least 50% of inferred tickers include local-exchange-listed companies
- **SC-006**: Inferred tickers span at least 2 supply chain layers for complex multi-sector themes

## Clarifications

### Session 2026-03-21

- Q: What confidence level threshold should trigger inclusion of an inferred ticker? → A: Qualitative categories (high/medium/low) from LLM judgment
- Q: When yfinance ticker validation fails, how should the system behave? → A: Return inferred tickers with "unverified" flag, let user decide
- Q: Where should smart ticker discovery be integrated in the pipeline? → A: Extend existing TickerAgent with sector inference logic

## Assumptions

- The LLM has sufficient training knowledge to identify sectors and infer relevant companies — this is expected given that major public companies in established sectors are well-represented in training data
- Market data verification (yfinance) is available and responsive for ticker validation
- The system targets well-known, established public companies for inference — not obscure micro-caps or recent IPOs
- Sector identification is limited to the LLM's knowledge; real-time sector classification databases are not required
- The existing pipeline structure (sequential agent execution) is preserved — smart discovery is integrated into the existing TickerAgent rather than adding a new agent
