# Feature Specification: Panel Chat & Language Selection

**Feature Branch**: `005-panel-chat-language`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "the progress should be shown in the side panel and people should be able to chat on the side panel based on the report and people can select the output language, so they can get the output with their native language"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-time Progress in Side Panel (Priority: P1)

While a report is being generated, the user sees live progress updates directly in the side panel. Each pipeline stage (extraction, entity detection, ticker mapping, thesis generation, critique, confidence scoring, data agent enrichment, formatting) is displayed as a step-by-step checklist. Completed stages show a checkmark, the current stage shows a spinner, and pending stages are greyed out. When data agents (news, fundamentals, macro) complete, a brief summary of their findings appears inline (e.g., "5 news articles found", "P/E: 36.8"). An elapsed timer counts seconds since generation started so the user knows the system is still working.

**Why this priority**: Without visible progress, users abandon the tool believing it is broken or frozen. This is the most critical UX gap.

**Independent Test**: Trigger report generation, open the side panel, and verify that stage checkmarks, agent result previews, a spinner on the active stage, and an elapsed timer all update in real time without requiring a page refresh.

**Acceptance Scenarios**:

1. **Given** a report generation is in progress, **When** the user opens the side panel, **Then** they see the current stage highlighted with a spinner, all completed stages with checkmarks, and pending stages greyed out.
2. **Given** a data agent finishes, **When** its results are ready, **Then** a one-line summary of findings appears under that agent's entry within 2 seconds.
3. **Given** generation is in progress, **When** the user watches the panel, **Then** an elapsed timer counts up every second showing how long generation has been running.
4. **Given** generation completes, **When** the final report is ready, **Then** the progress view automatically transitions to the full report view.

---

### User Story 2 - Chat with Report (Priority: P2)

After a report is generated, the user can ask follow-up questions about it using a chat interface embedded in the side panel. The chat uses the full report context (thesis, risks, tickers, news, fundamentals, macro data) to provide relevant answers. The user types a question, presses send, and receives a conversational response referencing specific sections of the report. Chat history persists for the current report and is visible as a scrollable conversation thread.

**Why this priority**: Users often want to dig deeper into specific aspects of a report (e.g., "Why is the confidence only 55%?", "What are the biggest risks?", "Explain the macro headwinds"). A chat interface transforms the report from a static document into an interactive analysis tool.

**Independent Test**: Generate a report, switch to the chat tab, type a question about the report content, and verify the response accurately references report data.

**Acceptance Scenarios**:

1. **Given** a completed report is displayed, **When** the user switches to the chat tab, **Then** they see a text input field, a send button, and an empty conversation area.
2. **Given** the chat is open, **When** the user types "What are the main risks?" and presses send, **Then** the system responds within 15 seconds with an answer that references the specific risks listed in the report.
3. **Given** an ongoing chat session, **When** the user asks a follow-up question, **Then** the system maintains conversational context from previous messages in the same session.
4. **Given** a chat is in progress, **When** the system is generating a response, **Then** a typing indicator is shown and the send button is disabled.
5. **Given** a completed report with no enrichment data, **When** the user asks about fundamentals, **Then** the chat responds acknowledging that fundamentals data was not available for this report.

---

### User Story 3 - Output Language Selection (Priority: P3)

The user can select their preferred output language from a dropdown in the extension settings. When a report is generated, all LLM-generated text (thesis, executive summary, risks, counter-thesis, confidence explanation, catalysts, limitations) is produced in the selected language. Chat responses also use the selected language. The language preference persists across sessions.

**Why this priority**: International users need reports in their native language to fully understand financial analysis. This expands the tool's accessibility to non-English speakers.

**Independent Test**: Set the output language to Korean in settings, generate a report, and verify that the thesis, risks, and other LLM-generated sections are in Korean while ticker symbols and numerical data remain unchanged.

**Acceptance Scenarios**:

1. **Given** the user opens extension settings, **When** they look at the settings form, **Then** they see a language dropdown with at least 10 language options including English (default), Korean, Japanese, Chinese (Simplified), Spanish, French, German, Portuguese, Hindi, and Arabic.
2. **Given** the user selects Korean as their output language, **When** they generate a new report, **Then** the thesis, executive summary, risks, counter-thesis, confidence explanation, catalysts, and limitations are all in Korean.
3. **Given** a language is selected, **When** the user closes and reopens the browser, **Then** the language preference is still set to the previously selected value.
4. **Given** Korean is selected as the output language, **When** the user chats with the report, **Then** the chat responses are in Korean.
5. **Given** any output language is selected, **When** a report is generated, **Then** ticker symbols (e.g., AAPL), numerical values (e.g., P/E: 36.8), and dates remain in their original format regardless of language.

---

### Edge Cases

- What happens when the user navigates away from the page during report generation? The generation continues in the background, and the side panel shows the final result when reopened.
- What happens when the chat request fails (network error, LLM timeout)? An error message appears in the chat thread with a "Retry" button.
- What happens when the user switches reports while a chat is active? The chat clears and starts fresh for the new report, with a brief notice that the previous chat was for a different report.
- What happens when the selected language is not well-supported by the LLM? The system falls back to producing output in English and displays a notice that the requested language may have limited quality.
- What happens when the user sends an empty chat message? The send button is disabled when the input is empty.
- What happens when the user selects a right-to-left language (e.g., Arabic)? The chat and report text direction adjusts to RTL for that content.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display real-time progress updates in the side panel during report generation, showing each pipeline stage's status (pending, active, completed).
- **FR-002**: System MUST show an elapsed timer during generation that counts seconds and minutes since the process started.
- **FR-003**: System MUST display brief result summaries for each completed data agent (news count, key metrics, sector info) within the progress view.
- **FR-004**: System MUST automatically transition from progress view to report view when generation completes.
- **FR-005**: System MUST provide a chat interface in the side panel accessible via a "Chat" tab after report generation is complete.
- **FR-006**: System MUST send the full report context (thesis, risks, tickers, enrichment data) along with user messages to provide context-aware chat responses.
- **FR-007**: System MUST display chat responses in a scrollable conversation thread with clear visual distinction between user and system messages.
- **FR-008**: System MUST maintain chat conversation history for the duration of the current report session.
- **FR-009**: System MUST provide a language selection dropdown in the extension settings page with at least 10 language options.
- **FR-010**: System MUST persist the selected language preference across browser sessions.
- **FR-011**: System MUST produce all LLM-generated report text in the selected output language.
- **FR-012**: System MUST produce chat responses in the selected output language.
- **FR-013**: System MUST preserve ticker symbols, numerical values, and dates in their original format regardless of output language.
- **FR-014**: System MUST show a typing indicator while a chat response is being generated.
- **FR-015**: System MUST disable the send button when the chat input is empty or when a response is being generated.

### Key Entities

- **Chat Message**: Represents a single message in the chat thread. Has a role (user or assistant), text content, and timestamp.
- **Chat Session**: A collection of chat messages tied to a specific report. Cleared when the user switches to a different report.
- **Language Preference**: The user's selected output language, stored as a locale code (e.g., "en", "ko", "ja"). Persisted in extension settings.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can see generation progress updates within 2 seconds of each stage completing.
- **SC-002**: 100% of generation sessions show a working elapsed timer that updates every second.
- **SC-003**: Users receive chat responses within 15 seconds of sending a message.
- **SC-004**: Chat responses reference specific report data (tickers, risks, thesis) at least 80% of the time when the question is about report content.
- **SC-005**: Users can change output language and generate a report in that language in under 30 seconds of interaction.
- **SC-006**: Language preference persists across 100% of browser restart cycles.
- **SC-007**: All LLM-generated text sections appear in the selected language for reports generated after a language change.

## Assumptions

- The existing side panel infrastructure (progress view, report rendering, tabs) is already in place and functional.
- The LLM provider supports generating text in all listed languages with reasonable quality.
- Chat does not require authentication beyond what is already configured for report generation (same provider, same API key).
- Chat conversation history is ephemeral (not persisted to disk) — it lasts only as long as the side panel stays open for that report.
- The language dropdown uses standard locale codes and English display names for each language.

## Out of Scope

- Translation of previously generated reports (only new reports use the selected language).
- Voice input or speech-to-text for chat.
- Multi-user chat or collaborative features.
- Chat export or sharing functionality.
- Custom language/locale additions beyond the predefined list.
