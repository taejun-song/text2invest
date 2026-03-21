# Feature Specification: User Ticker Input

**Feature Branch**: `010-user-ticker-input`
**Created**: 2026-03-21
**Status**: Draft
**Input**: User description: "the input interface of the user provided tickers"

## Clarifications

### Session 2026-03-21

- Q: How should multiple tickers be presented in the input field? → A: Tag/chip style - each ticker becomes a removable chip in the field

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add Tickers Before Generation (Priority: P1)

When a user selects text for analysis, they can optionally add their own ticker symbols before generating the report. This ensures that even if the selected text doesn't mention specific companies, the user can still get analysis for securities they're interested in.

**Why this priority**: This is the core functionality that enables user-specified tickers, providing immediate value when LLM inference fails or when users want specific securities analyzed.

**Independent Test**: Can be fully tested by selecting text, adding ticker symbols in the input field, and generating a report. The added tickers appear in the final report.

**Acceptance Scenarios**:

1. **Given** the sidepanel is open and text is selected, **When** user types a ticker symbol and clicks generate, **Then** the report includes the user-specified ticker alongside any LLM-detected tickers.
2. **Given** the ticker input field is visible, **When** user enters multiple tickers (each appearing as a chip), **Then** all entered tickers are sent to the server for analysis.
3. **Given** the ticker input field is empty, **When** user clicks generate, **Then** the system proceeds with LLM-detected tickers only (existing behavior).

---

### User Story 2 - Ticker Validation Feedback (Priority: P2)

Users receive immediate feedback about the validity of entered ticker symbols, helping them correct errors before generation.

**Why this priority**: Improves user experience by preventing failed generations due to invalid ticker formats, but the system can still function without this validation.

**Independent Test**: Can be tested by entering various valid and invalid ticker formats and observing the visual feedback.

**Acceptance Scenarios**:

1. **Given** the ticker input field, **When** user enters a valid ticker format (e.g., "AAPL"), **Then** no error indication is shown.
2. **Given** the ticker input field, **When** user enters an invalid format (e.g., "aapl123456789"), **Then** visual feedback indicates the format is invalid.
3. **Given** the ticker input has validation errors, **When** user clicks generate, **Then** the generate action is blocked until errors are fixed.

---

### User Story 3 - Ticker Autocomplete (Priority: P3)

Users can search for tickers by company name and receive suggestions, making it easier to find the correct ticker symbol.

**Why this priority**: Enhances usability for users who don't know exact ticker symbols, but the feature is fully functional without it.

**Independent Test**: Can be tested by typing a company name and observing autocomplete suggestions appear.

**Acceptance Scenarios**:

1. **Given** the ticker input field, **When** user types "Apple", **Then** suggestions appear showing "AAPL - Apple Inc."
2. **Given** suggestions are visible, **When** user clicks a suggestion, **Then** the ticker is added to the input.
3. **Given** network is unavailable, **When** user types a search term, **Then** no suggestions appear and user can still manually enter tickers.

---

### Edge Cases

- What happens when user enters duplicate tickers? System should deduplicate silently.
- What happens when user enters a ticker that's also detected by LLM? System should deduplicate, keeping user-provided version.
- What happens when ticker input contains extra whitespace or lowercase letters? System should normalize input (trim whitespace, uppercase conversion).
- How does system handle international ticker formats (e.g., "005930.KS")? System should accept exchange suffix patterns.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a ticker input field in the sidepanel when text is selected for analysis.
- **FR-002**: System MUST display entered tickers as removable tag/chip elements in the input field.
- **FR-003**: System MUST normalize ticker input by trimming whitespace and converting to uppercase.
- **FR-004**: System MUST validate ticker format against the pattern `^[A-Z0-9.\-]{1,12}$` before submission.
- **FR-005**: System MUST include user-provided tickers in the generation request to the server.
- **FR-006**: System MUST display user-provided tickers in the report with a "user-provided" indicator.
- **FR-007**: System MUST deduplicate tickers when user-provided tickers overlap with LLM-detected tickers.
- **FR-008**: System MUST preserve existing generation flow when no user tickers are provided.
- **FR-009**: System MUST support international ticker formats including exchange suffixes (.KS, .T, .HK, etc.).
- **FR-010**: System MUST provide visual feedback for invalid ticker formats before generation.

### Key Entities

- **UserTicker**: Represents a ticker symbol provided by the user with optional company name.
- **TickerInput**: The UI component that captures user ticker input, handles validation and normalization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully add custom tickers and see them in generated reports 100% of the time when format is valid.
- **SC-002**: Invalid ticker formats are caught before generation in 100% of cases.
- **SC-003**: Time to add tickers does not exceed 10 seconds for typical use (1-5 tickers).
- **SC-004**: User-provided tickers are clearly distinguishable from LLM-detected tickers in the report.
- **SC-005**: System handles edge cases (duplicates, whitespace, case) without user intervention.

## Assumptions

- Users are familiar with stock ticker symbol conventions (uppercase letters, exchange suffixes for international markets).
- The existing backend support for `user_tickers` parameter is already implemented (from spec 009).
- Autocomplete suggestions (P3) would use the same `ticker_search` tool that exists in the backend.
- The input field will be collapsible or non-intrusive to avoid cluttering the UI for users who don't need it.
