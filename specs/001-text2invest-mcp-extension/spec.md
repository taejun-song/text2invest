# Feature Specification: Text2Invest

**Feature Branch**: `001-text2invest-mcp-extension`
**Created**: 2026-02-11
**Status**: Draft
**Input**: Browser extension + MCP server that converts user-selected text into structured, uncertainty-aware investment ideas

## Overview

Text2Invest enables users to highlight any text on the web and receive a structured, educational investment hypothesis. The system is privacy-first, model-agnostic, and grounded strictly in the selected text. A multi-stage AI agent pipeline orchestrated by an MCP (Model Control Plane) server ensures transparency, schema validation, and extensibility.

**Primary Users**: Knowledge workers, researchers, investors reading articles, papers, reports, filings, or social media who want interpretable investment hypotheses rather than black-box answers.

**Core Flow**: User highlights text → Selection stabilizes → Extension sends request to MCP server → MCP orchestrates multi-stage agents → Structured investment idea returned → User reviews, saves, rates, exports.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Investment Idea from Selected Text (Priority: P1)

A user reading a news article about a company's earnings highlights a paragraph describing revenue growth and new product launches. After the selection stabilizes, they click "Generate idea" and receive a structured investment hypothesis with identified tickers, thesis, risks, and confidence score.

**Why this priority**: Core value proposition. Without this, the product has no function.

**Independent Test**: Can be fully tested by selecting text on any webpage, triggering generation, and verifying a valid structured report is returned.

**Acceptance Scenarios**:

1. **Given** user has the extension installed, **When** user selects 50 characters of text and clicks "Generate idea", **Then** system returns a structured investment report within 30 seconds
2. **Given** user selects text mentioning a company, **When** generation completes, **Then** report includes at least one ticker symbol with confidence score
3. **Given** user selects text, **When** generation is in progress, **Then** user can cancel the request and UI returns to idle state
4. **Given** user selects fewer than 20 characters, **When** selection stabilizes, **Then** popup displays message indicating minimum length requirement

---

### User Story 2 - View and Navigate Full Report (Priority: P2)

After generation completes, user opens the full report in a side panel to review executive summary, rationale with quoted text, catalysts, risks, counter-thesis, and confidence explanation. User can expand/collapse sections and see which parts of the original text support each claim.

**Why this priority**: Enables informed decision-making through transparency. Essential for trust in AI-generated content.

**Independent Test**: Can be tested by generating a report and verifying all required sections are present and text quotes link back to source offsets.

**Acceptance Scenarios**:

1. **Given** a completed report, **When** user clicks "Open full report", **Then** side panel displays all required sections (executive summary, tickers, rationale, catalysts, risks, counter-thesis, horizon, confidence)
2. **Given** full report is open, **When** user views rationale section, **Then** each supporting quote shows the exact text from the original selection
3. **Given** full report is open, **When** user scrolls, **Then** disclaimer "Educational only - Not financial advice" is visible

---

### User Story 3 - Save and Search History (Priority: P3)

User generates multiple investment ideas over several days. They can browse their history, search by ticker symbol, source site, or date, and re-open any previously generated report.

**Why this priority**: Enables building a personal research library. Increases long-term product value.

**Independent Test**: Can be tested by generating 3+ reports, then searching for a specific ticker and verifying correct results appear.

**Acceptance Scenarios**:

1. **Given** user has generated 5 reports, **When** user opens history view, **Then** all 5 reports are listed in reverse chronological order
2. **Given** user has reports for AAPL and TSLA, **When** user searches for "AAPL", **Then** only AAPL-related reports appear
3. **Given** user views history, **When** user clicks on a past report, **Then** full report opens with all original data

---

### User Story 4 - Export Report (Priority: P4)

User wants to share an investment idea with colleagues or save to their notes system. They can export any report as Markdown or JSON.

**Why this priority**: Extends utility beyond the browser. Enables integration with external workflows.

**Independent Test**: Can be tested by exporting a report and verifying the output file is valid Markdown/JSON containing all report sections.

**Acceptance Scenarios**:

1. **Given** a completed report, **When** user clicks export and selects Markdown, **Then** system downloads a .md file with all sections and disclaimer
2. **Given** a completed report, **When** user clicks export and selects JSON, **Then** system downloads a .json file matching the IdeaReport schema

---

### User Story 5 - Configure LLM Provider (Priority: P5)

User prefers to use their own API key with a specific provider (OpenAI, Anthropic, or local Ollama). They can configure provider, model, and temperature in extension settings.

**Why this priority**: Enables model-agnostic operation and privacy-conscious local processing.

**Independent Test**: Can be tested by configuring a different provider and verifying generation uses the selected provider.

**Acceptance Scenarios**:

1. **Given** user opens settings, **When** user selects Anthropic as provider and enters API key, **Then** subsequent generations use Anthropic models
2. **Given** user configures Ollama with local endpoint, **When** user generates an idea, **Then** no data is sent to external services
3. **Given** no provider is configured, **When** user attempts to generate, **Then** system prompts user to configure a provider first

---

### User Story 6 - Rate and Provide Feedback (Priority: P6)

User wants to indicate whether a generated idea was useful and optionally explain why. This feedback is stored locally for future aggregation potential.

**Why this priority**: Enables learning loop and quality improvement over time.

**Independent Test**: Can be tested by rating a report and verifying the rating persists in local storage.

**Acceptance Scenarios**:

1. **Given** a completed report, **When** user clicks "useful", **Then** rating is saved locally and UI reflects the rating
2. **Given** user rated "not useful", **When** user adds note "Missing key risk factor", **Then** note is saved with the rating

---

### Edge Cases

- What happens when selected text exceeds 8,000 characters? System truncates to 8,000 characters and displays notice to user.
- What happens when selected text contains no identifiable companies or investment-relevant content? System returns report with empty tickers array and low confidence score with explanation.
- What happens when LLM provider is unreachable? System displays error with retry option and suggests checking API key/network.
- What happens when LLM returns invalid JSON? System retries up to 3 times with validation feedback, then displays schema error to user.
- What happens when user has no API key configured? Generation is blocked with prompt to configure provider in settings.
- What happens on rate-limited API calls? System displays rate limit error with estimated wait time if available.
- What happens when user navigates away during generation? In-flight request is cancelled and no report is stored.

## Requirements *(mandatory)*

### Functional Requirements

**Selection & Triggering**
- **FR-001**: System MUST detect text selection via mouse drag or keyboard selection
- **FR-002**: System MUST wait at least 600ms after selection stabilizes before enabling trigger
- **FR-003**: System MUST enforce minimum selection length of 20 characters
- **FR-004**: System MUST truncate selections exceeding 8,000 characters and notify user
- **FR-005**: System MUST display selection popup near highlighted text when selection is valid

**Generation & Processing**
- **FR-006**: System MUST send only selected text, page URL, and page title to MCP server
- **FR-007**: System MUST execute multi-stage agent pipeline (Extraction → Entity → Ticker → Thesis → Critique → Confidence → Formatter)
- **FR-008**: Each agent stage MUST emit structured JSON validated against its schema
- **FR-009**: System MUST reject and regenerate invalid JSON outputs (max 3 retries per stage)
- **FR-010**: System MUST support cancellation of in-flight requests
- **FR-011**: System MUST provide loading indicator during generation

**Output & Display**
- **FR-012**: System MUST return IdeaReport matching the frozen schema (id, created_at, source, tickers, thesis, rationale_quotes, catalysts, risks, counter_thesis, horizon, confidence_score, confidence_explanation, limitations, provider_meta)
- **FR-013**: System MUST display executive summary with maximum 3 bullet points
- **FR-014**: System MUST display confidence score as value between 0 and 1 with explanation
- **FR-015**: System MUST show text-grounded rationale with exact quotes and character offsets
- **FR-016**: System MUST display mandatory disclaimer "Educational only - Not financial advice" in UI and exports

**History & Storage**
- **FR-017**: System MUST store all generated reports locally on user device
- **FR-018**: System MUST support searching history by ticker symbol, source site, and date
- **FR-019**: System MUST export reports as Markdown or JSON formats
- **FR-020**: System MUST preserve all report data in exports including disclaimer

**Provider Configuration**
- **FR-021**: System MUST support OpenAI-compatible, Anthropic-compatible, and Ollama providers
- **FR-022**: System MUST allow user to configure provider, model, and temperature
- **FR-023**: System MUST store API keys locally only, never logging or exporting them
- **FR-024**: System MUST never perform web browsing/lookup unless explicitly enabled by user (default OFF)

**Privacy & Security**
- **FR-025**: System MUST redact detected PII (emails, phone numbers) from selected text by default
- **FR-026**: System MUST request only minimal browser permissions required for functionality
- **FR-027**: System MUST NOT persistently mutate webpage content

**Evaluation**
- **FR-028**: System MUST allow users to rate reports as "useful" or "not useful"
- **FR-029**: System MUST allow optional text notes with ratings
- **FR-030**: System MUST store ratings locally with associated report

### Key Entities

- **IdeaReport**: Core output entity containing structured investment hypothesis. Includes unique ID, creation timestamp, source information (URL, title), original selection text, identified tickers with confidence, thesis statement, supporting quotes with text offsets, catalysts, risks, counter-thesis, time horizon, overall confidence score with explanation, limitations, and provider metadata.

- **Ticker**: Identified security with symbol, company name, and confidence score (0-1) indicating certainty of the mapping.

- **RationaleQuote**: Text excerpt from original selection supporting the thesis. Includes exact quote string, start offset, and end offset for source highlighting.

- **UserSettings**: User configuration including selected provider, model name, temperature parameter, and feature toggles (PII redaction, web lookup).

- **Evaluation**: User feedback on a report including rating (useful/not_useful), optional notes explaining the rating, and timestamp.

- **AgentOutput**: Intermediate structured output from each pipeline stage, validated against stage-specific schema before passing to next agent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate a complete investment idea from selected text in under 30 seconds (for texts under 2,000 characters)
- **SC-002**: 90% of generated reports include at least one relevant ticker when source text mentions identifiable companies
- **SC-003**: All generated reports pass schema validation with no missing required fields
- **SC-004**: Users can find any previously generated report within 10 seconds using search
- **SC-005**: Exported Markdown and JSON files contain all report sections and mandatory disclaimer
- **SC-006**: Users can successfully configure and switch between all three supported providers (OpenAI, Anthropic, Ollama)
- **SC-007**: System handles provider errors gracefully with clear error messages and retry options
- **SC-008**: No user PII (emails, phone numbers) appears in transmitted data when redaction is enabled (default)
- **SC-009**: Extension functions correctly on Chrome and Edge browsers
- **SC-010**: Users can cancel in-flight requests and UI returns to idle state within 1 second

## Assumptions

- Users will provide their own API keys for cloud LLM providers
- Selected text is in English (multi-language support deferred to future version)
- Users have stable internet connection for cloud provider usage
- Browser extension runs in foreground context (no background processing required for MVP)
- MCP server can run locally or as cloud service depending on deployment choice

## Known Limitations

- Mobile browser support is limited due to platform constraints (no true background auto-trigger on iOS/Chrome mobile)
- Auto-trigger with countdown is v1 feature, MVP uses manual trigger only
- Multi-provider support with live switching is v1 feature, MVP focuses on single configured provider
- Real-time collaboration and cloud sync are future features, not in scope for MVP or v1
- Safari Web Extension and iOS Share Sheet support is v1.1 scope
