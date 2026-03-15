# Feature Specification: Thinking Mode Toggle & Display

**Feature Branch**: `004-thinking-mode-panel`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "What about we toggle the thinking mode? At least show the thinking process in the open panel, and I need the button to open the panel from the extension."

## Clarifications

### Session 2026-03-15

- Q: Should thinking tokens be displayed as a single stream, per-agent, or grouped by phase? → A: Grouped by phase — parallel agents' thinking shown together, then sequential agents' thinking shown in order.
- Q: Should thinking mode default to enabled or disabled for new installations? → A: Disabled by default. Users opt in to see the thinking process.
- Q: Should thinking output be included in Markdown/JSON exports? → A: Yes, as a collapsible/separate section (Markdown `<details>` block, JSON nested field).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Show Thinking Process in Side Panel (Priority: P1)

When the LLM is generating an investment report, the user wants to see the model's internal reasoning/thinking process streamed in real-time within the side panel. This provides transparency into how the AI arrives at its conclusions and reduces perceived wait time during long generation cycles.

**Why this priority**: The thinking process is the core value proposition. Without it, the user stares at a spinner with no insight into what the AI is doing. Showing reasoning builds trust and keeps users engaged during the multi-agent pipeline.

**Independent Test**: Can be tested by selecting text, triggering generation, and observing the thinking tokens appearing in real-time in the side panel before the final report renders.

**Acceptance Scenarios**:

1. **Given** a generation is in progress, **When** the LLM produces thinking/reasoning tokens, **Then** the side panel displays them grouped by pipeline phase: parallel agents' thinking shown together under a "Parallel Analysis" group, then sequential agents' thinking shown in order under their respective labels, each in a collapsible section with a distinct visual style (italic, muted color).
2. **Given** thinking tokens are streaming, **When** the user scrolls through the thinking output, **Then** auto-scroll pauses; when the user scrolls back to the bottom, auto-scroll resumes.
3. **Given** a generation completes, **When** the final report is ready, **Then** the thinking section remains accessible (collapsed by default) above the report so the user can review the reasoning that led to the conclusions.
4. **Given** the LLM does not produce thinking tokens (e.g., non-reasoning model), **When** generation proceeds, **Then** the thinking section is hidden and the panel behaves as before.

---

### User Story 2 - Toggle Thinking Mode On/Off (Priority: P2)

The user wants a toggle to enable or disable the LLM's thinking/reasoning mode. When enabled, the model spends tokens on internal reasoning before responding, producing higher-quality but slower output. When disabled, the model responds directly without a thinking phase, producing faster but potentially less thorough output.

**Why this priority**: Gives users control over the quality-speed tradeoff. Some users may prefer faster results for simple queries, while others want deep reasoning for complex investment analysis.

**Independent Test**: Can be tested by toggling the setting in the extension options, generating a report, and confirming the LLM response includes or excludes thinking tokens based on the toggle state.

**Acceptance Scenarios**:

1. **Given** the user is on the extension settings page, **When** they toggle "Thinking Mode" on, **Then** the preference is saved and subsequent generations include the thinking/reasoning phase.
2. **Given** thinking mode is disabled, **When** a report is generated, **Then** no thinking tokens are produced or displayed, and generation completes faster.
3. **Given** the user changes the toggle mid-session, **When** they generate a new report, **Then** the new setting takes effect immediately (does not affect in-progress generations).

---

### User Story 3 - Open Side Panel from Extension UI (Priority: P3)

The user wants a dedicated button in the extension popup to open the side panel at any time, not just during generation. This allows viewing previous reports, checking generation progress, or accessing the panel without needing to trigger a new generation.

**Why this priority**: Convenience feature that improves navigation. Currently the side panel only opens programmatically during generation from the floating tooltip; there's no manual way to open it from the popup.

**Independent Test**: Can be tested by clicking the "Open Panel" button in the popup and confirming the side panel opens regardless of generation state.

**Acceptance Scenarios**:

1. **Given** the extension popup is open, **When** the user clicks "Open Panel", **Then** the side panel opens for the current tab.
2. **Given** the side panel is already open, **When** the user clicks "Open Panel" again, **Then** the panel remains open (no error, no duplicate).
3. **Given** a previous report exists in storage, **When** the user opens the panel via the button, **Then** the last report or current generation state is displayed.

---

### Edge Cases

- What happens when the LLM returns thinking tokens in an unexpected format (not separated from content)?
- How does the system handle extremely long thinking output (thousands of tokens) without degrading panel performance?
- What happens when the user toggles thinking mode while a generation is in progress?
- What happens when the model provider does not support thinking/reasoning mode (e.g., non-qwen models)?
- How does the panel behave when opened via the button while no report or generation exists (first-time use)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST stream thinking/reasoning tokens from the LLM to the side panel in real-time during generation.
- **FR-002**: System MUST display thinking tokens grouped by pipeline phase: parallel agents' thinking shown together, then sequential agents' thinking shown in order, each in a labeled collapsible section separate from the final report.
- **FR-003**: System MUST auto-scroll the thinking section as new tokens arrive, pausing auto-scroll when the user manually scrolls up.
- **FR-004**: System MUST provide a "Thinking Mode" toggle in the extension settings (options page).
- **FR-005**: System MUST persist the thinking mode preference across browser sessions, defaulting to disabled for new installations.
- **FR-006**: System MUST pass the thinking mode preference to the LLM provider when making API calls, controlling whether reasoning tokens are generated.
- **FR-007**: System MUST hide the thinking section when thinking mode is disabled or when the model does not produce thinking tokens.
- **FR-008**: System MUST provide an "Open Panel" button in the extension popup that opens the side panel for the active tab.
- **FR-009**: System MUST retain the thinking output alongside the report in history so users can review past reasoning.
- **FR-011**: System MUST include thinking output in exports as a collapsible section (Markdown `<details>` block) or nested field (JSON), keeping the final report as the primary content.
- **FR-010**: System MUST gracefully handle models that do not support thinking mode by falling back to standard generation without error.

### Key Entities

- **ThinkingChunk**: A fragment of the model's reasoning output, streamed in real-time. Contains the text content, the originating agent identifier, and the pipeline phase (parallel or sequential).
- **ThinkingModePreference**: A user setting (boolean, default: false) indicating whether thinking/reasoning mode is enabled. When opted in, the thinking process is streamed and displayed in the panel. Stored in extension settings alongside provider configuration.
- **GenerationState (extended)**: The existing generation state, extended with fields for thinking content and thinking mode status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can see the first thinking token within 2 seconds of generation starting (when thinking mode is enabled and the model supports it).
- **SC-002**: Thinking output renders without visible lag or jank for outputs up to 10,000 tokens.
- **SC-003**: Users can toggle thinking mode and see the change reflected in the next generation within one interaction.
- **SC-004**: Users can open the side panel from the popup in under 1 second.
- **SC-005**: 100% of supported model providers gracefully handle thinking mode toggle (no errors when provider doesn't support it).

## Assumptions

- The qwen3/Qwen3.5 model currently in use supports a thinking/reasoning mode that produces separate thinking tokens before the final content.
- Qwen3 models embed thinking as `<think>...</think>` tags in streamed content. The server parses these tags directly rather than relying on LiteLLM's `reasoning_content` field, which is unreliable in streaming mode.
- The SSE streaming infrastructure already in place (from feature 003) can be extended to include thinking token events.
- The `chrome.sidePanel.open()` API is available and works when called from the popup context (user gesture present).
