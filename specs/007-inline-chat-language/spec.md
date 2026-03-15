# Feature Specification: Inline Chat & Language Reliability

**Feature Branch**: `007-inline-chat-language`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "Ensure that each report is generated in a right language, and chat feature should be in the report tab. Do not separate the tab for user experience"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inline Chat within Report View (Priority: P1)

Currently the chat feature lives in a separate "Chat" tab, forcing users to leave the report to ask follow-up questions. Instead, the chat input should appear directly at the bottom of the report view — always visible while reading the report. Users read a section, have a question, type it immediately without switching tabs. The chat thread expands inline below the report content, keeping the full context visible.

**Why this priority**: A separate chat tab breaks the user's reading flow. When asking "What does this risk mean?", the user needs to see the report while chatting. An inline chat provides a seamless experience — contextual, non-disruptive, always available.

**Independent Test**: Generate a report, scroll through the report content, and verify a chat input bar is pinned at the bottom of the report view. Type a question, verify the response appears inline below the report without navigating away. The separate Chat tab no longer exists.

**Acceptance Scenarios**:

1. **Given** a report is displayed in the side panel, **When** the user looks at the report view, **Then** a chat input bar is visible at the bottom of the report without switching tabs.
2. **Given** a user types a question in the inline chat and presses Send, **When** the response arrives, **Then** the chat thread expands below the report content and the user can still scroll up to see the report.
3. **Given** no report is loaded, **When** the user views the side panel, **Then** the chat input is not visible (it only appears when a report exists).
4. **Given** a user switches to a different report (from history), **When** the new report loads, **Then** the previous chat thread is cleared and a fresh input is shown for the new report.
5. **Given** report generation is in progress, **When** the progress view is displayed, **Then** the chat input is hidden until the report completes.

---

### User Story 2 - Reliable Language Output (Priority: P2)

When a user selects an output language (e.g., Korean), every text element in the generated report must actually be in that language — thesis, executive summary, risks, counter-thesis, catalysts, limitations, confidence explanation, and chat responses. Currently the language instruction is appended to agent prompts, but some agents may ignore it or produce mixed-language output. This story ensures language consistency is verified and enforced.

**Why this priority**: A partially translated report (some sections in English, some in Korean) is worse than a fully English report. Users who select a language expect consistent output across all sections. This is a reliability fix for an existing feature.

**Independent Test**: Set output language to Korean, generate a report about an English-language article, and verify every text section (thesis, summary, risks, catalysts, counter-thesis, confidence explanation, limitations) is in Korean. Ticker symbols and numbers remain in English.

**Acceptance Scenarios**:

1. **Given** the output language is set to Korean, **When** a report generates from English-language source text, **Then** the thesis, executive summary, risks, catalysts, counter-thesis, confidence explanation, and limitations are all in Korean.
2. **Given** the output language is set to Japanese, **When** a user asks a question in the inline chat, **Then** the assistant's response is in Japanese.
3. **Given** the output language is set to a non-English language, **When** the report generates, **Then** ticker symbols (e.g., AAPL), numbers (e.g., 78%), dates, and JSON structure remain in English/universal format.
4. **Given** the output language is set to English (default), **When** a report generates, **Then** no language instruction is injected and output is naturally in English.
5. **Given** an agent produces output that mixes languages despite the language instruction, **When** the formatter assembles the final report, **Then** the formatter re-applies the language instruction to ensure consistency in the final output.

---

### Edge Cases

- What happens when the chat input is submitted while the user is scrolled to the middle of a long report? The view scrolls to the chat thread area to show the response, but the user can scroll back up to the report.
- What happens when the chat thread grows very long? The chat thread is limited to a maximum visible height with its own scroll, so it doesn't push the report off screen.
- What happens when the selected language uses a different script (Arabic RTL, Chinese characters)? The report and chat sections apply appropriate text direction and font rendering for the selected language.
- What happens when the source text is already in the target language? The system generates the report in the target language as usual — no special handling needed.
- What happens when a collaborative agent (news, fundamentals) returns data in English despite the language instruction? The synthesis/formatter stage translates summary text while preserving raw data values (metrics, dates, URLs) in their original format.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Chat tab MUST be removed from the side panel tab bar. Only "Report" and "History" tabs remain.
- **FR-002**: A chat input bar MUST appear at the bottom of the report view when a report is loaded, pinned so it remains visible while scrolling the report.
- **FR-003**: Chat messages MUST appear in a collapsible thread section between the report content and the input bar.
- **FR-004**: The chat thread section MUST be collapsible/expandable so users can hide it to focus on the report.
- **FR-005**: The chat input bar MUST be hidden when no report is loaded or when report generation is in progress.
- **FR-006**: The chat thread MUST clear when the user switches to a different report.
- **FR-007**: All existing chat functionality (send message, typing indicator, error with retry, Enter key to send) MUST be preserved in the inline implementation.
- **FR-008**: The language instruction MUST be enforced at the formatting stage — the formatter agent MUST verify and correct language consistency before producing the final report.
- **FR-009**: Every user-facing text field in the report (thesis, executive_summary, risks, catalysts, counter_thesis, confidence_explanation, limitations) MUST be in the selected output language.
- **FR-010**: Chat responses MUST be in the selected output language.
- **FR-011**: Ticker symbols, numerical values, dates, URLs, and JSON keys MUST remain in English/universal format regardless of output language.
- **FR-012**: The inline chat MUST have a maximum height with its own scrollbar to prevent the chat from pushing the report out of view.

### Key Entities

- **InlineChatThread**: A chat conversation embedded within the report view, tied to a specific report ID. Contains an ordered list of messages and a collapsed/expanded state.
- **LanguageEnforcementRule**: The set of fields that must be translated (text fields) versus preserved (symbols, numbers, keys) when a non-English output language is selected.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can ask follow-up questions about a report without leaving the report view.
- **SC-002**: The side panel has exactly 2 tabs (Report, History) — no separate Chat tab.
- **SC-003**: When output language is set to a non-English language, 100% of user-facing text fields in the report are in the selected language.
- **SC-004**: Chat responses match the selected output language 100% of the time.
- **SC-005**: The inline chat thread does not exceed 40% of the viewport height, preserving report visibility.
- **SC-006**: Users can collapse the chat thread to see the full report without the chat taking up space.

## Assumptions

- The existing chat backend (POST /api/v1/chat) does not need changes — only the frontend placement moves from a separate tab to inline within the report view.
- Language enforcement at the formatter stage may require an additional LLM call for verification/translation if upstream agents produce mixed-language output. This is acceptable as a trade-off for consistency.
- The inline chat replaces the separate chat tab entirely — there is no option to use the old tab-based layout.
- The chat input bar uses the same styling and behavior as the current implementation, just repositioned within the report view.
