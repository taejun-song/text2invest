# Tasks: Panel Chat & Language Selection

**Input**: Design documents from `/specs/005-panel-chat-language/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Foundational (Shared Model Changes)

**Purpose**: Type and model updates needed by multiple user stories

- [x] T001 [P] Add `output_language: str | None = Field(None)` field to `UserSettings` in `packages/mcp-server/src/models/idea_report.py`. Default to `None` (treated as English when None).
- [x] T002 [P] Add `ChatMessage` interface (`role: 'user' | 'assistant'`, `content: string`, `timestamp: string`) and add `output_language?: string` to `UserSettings` interface in `packages/extension/src/types/index.ts`.
- [x] T003 [P] Add `output_language: 'en'` to `DEFAULT_SETTINGS` in `packages/extension/src/lib/storage.ts`.

**Checkpoint**: Shared types ready — user story implementation can begin.

---

## Phase 2: User Story 1 — Real-time Progress in Side Panel (Priority: P1)

**Goal**: Users see live progress updates with stage checklist, agent result previews, and elapsed timer during report generation.

**Independent Test**: Trigger report generation, open side panel, verify stage checkmarks appear, spinner on active stage, agent summaries inline, timer counts up in mm:ss, and view auto-transitions to report on completion.

**Note**: The existing `renderProgress()` in panel.ts already implements most of this (stage list, spinners, checkmarks, agent result previews, elapsed timer, auto-transition). This phase is a verification and polish pass.

### Implementation

- [x] T004 [US1] In `packages/extension/src/sidepanel/panel.ts`, verify the elapsed timer displays mm:ss format (e.g., "2:34" not "154s"). If the current `updateElapsed()` method uses raw seconds, update it to format as `Math.floor(s/60):padded_seconds`. Ensure the timer starts when `started_at` is set and clears when generation completes.
- [x] T005 [US1] In `packages/extension/src/sidepanel/panel.ts`, verify `renderProgress()` shows all 8 pipeline stages in order: Extraction, Entity Detection, Ticker Mapping, Thesis Generation, Critique, Confidence Scoring, Enrichment (with sub-agents), Formatting. Ensure completed stages show "✓", current stage shows spinner, pending stages show "○". Verify auto-transition to report view when `status === 'completed'` fires via `chrome.storage.onChanged`.

**Checkpoint**: Progress display verified — all FR-001 through FR-004 confirmed working.

---

## Phase 3: User Story 2 — Chat with Report (Priority: P2)

**Goal**: Users can ask follow-up questions about a generated report via a chat interface in the side panel.

**Independent Test**: Generate a report, click Chat tab, type "What are the main risks?", press Send, verify response references report risks within 15 seconds.

### Implementation

- [x] T006 [US2] Add `POST /api/v1/chat` endpoint to `packages/mcp-server/src/api_server.py`. Create a Pydantic `ChatRequest` model with fields: `report_context` (dict with id, tickers, thesis, executive_summary, risks, counter_thesis, confidence_score, confidence_explanation, catalysts, limitations, and optional news_context/fundamentals_summary/macro_context as strings), `messages` (list of dicts with role/content), `user_settings` (UserSettings). Build a system prompt from report_context that says "You are an investment analysis assistant. Answer questions about this report:" followed by a formatted summary of the report. Append language instruction if `output_language` is set and not "en". Send system prompt + messages to `LLMProvider.complete()`. Return `{"role": "assistant", "content": response, "timestamp": now_iso}`.
- [x] T007 [US2] Add `chatWithReport(reportContext, messages, settings)` function to `packages/extension/src/lib/api.ts`. POST to `/api/v1/chat` with the three parameters. Return the parsed `ChatMessage` response. Handle errors by throwing `ApiError`.
- [x] T008 [US2] Add Chat tab and chat UI to `packages/extension/src/sidepanel/index.html`. Add a third tab button `<button id="tab-chat" class="tab">Chat</button>` in the `.tabs` div. Add `<div id="chat-view" class="hidden">` containing: a scrollable `.chat-messages` container, a `.chat-input-bar` with `<input type="text" id="chat-input" placeholder="Ask about this report...">` and `<button id="chat-send" class="btn btn-primary" disabled>Send</button>`. Add CSS for: `.chat-messages` (flex column, overflow-y auto, max-height calc(100vh - 180px)), `.chat-bubble.user` (blue background, white text, align right), `.chat-bubble.assistant` (grey background, align left), `.chat-input-bar` (flex, gap 8px, padding, border-top), `.typing-indicator` (three animated dots), `.chat-error` (red text with retry button).
- [x] T009 [US2] Implement chat logic in `packages/extension/src/sidepanel/panel.ts`. Add a `chatMessages: ChatMessage[]` array and `chatReportId: string | null` to `PanelController`. Add `showTab()` logic for the "chat" tab (show chat-view, hide others, set active tab). In `initChat()`: when chat tab is clicked and a report exists, show the chat view. `sendMessage()`: read input value, disable send button, add user bubble to DOM, show typing indicator, call `chatWithReport()` with report context built from `this.currentReport` (flatten enrichment data to summary strings), the messages array, and current settings. On response: remove typing indicator, add assistant bubble, re-enable send button, scroll to bottom. On error: show error message in thread with a "Retry" button. Clear chat when `this.currentReport` changes (compare report IDs) and show a system message "Chat cleared — you switched to a different report." in the thread. Disable send button when input is empty (listen to `input` event). Support Enter key to send.
- [x] T010 [US2] Disable Chat tab when no report is loaded or generation is in progress. In `packages/extension/src/sidepanel/panel.ts`, in the state update handler: if `status === 'generating'` or no `currentReport`, add `disabled` class to `#tab-chat` and prevent switching. When report is available, remove `disabled` class.

**Checkpoint**: Chat with report fully functional — FR-005 through FR-008, FR-014, FR-015 confirmed.

---

## Phase 4: User Story 3 — Output Language Selection (Priority: P3)

**Goal**: Users can select an output language in settings; all LLM-generated text in reports and chat responses is produced in that language.

**Independent Test**: Set output language to Korean in settings, generate a report, verify thesis/risks/summary are in Korean while ticker symbols remain in English.

### Implementation

- [x] T011 [P] [US3] Add language dropdown to `packages/extension/src/options/index.html`. Insert a new `.card` section titled "Output Language" before the "Advanced" card. Add a `<select id="output-language">` with options: English (en), Korean (ko), Japanese (ja), Chinese Simplified (zh), Spanish (es), French (fr), German (de), Portuguese (pt), Hindi (hi), Arabic (ar). Add helper text: "Reports and chat responses will be generated in this language."
- [x] T012 [P] [US3] Handle language selection in `packages/extension/src/options/options.ts`. Add `outputLanguageSelect` as a class property pointing to `#output-language`. In `loadSettings()`, set its value from `settings.output_language || 'en'`. In `handleSave()`, add `output_language: this.outputLanguageSelect.value` to the saved settings object. In `handleReset()`, reset it to `'en'`.
- [x] T013 [US3] Inject language instruction into sequential agent system prompts in `packages/mcp-server/src/agents/base.py`. In the `run()` method, after getting the system prompt via `self.get_system_prompt()`, check `self.settings.output_language`. If it is set and not `"en"` and not `None`, append to the system prompt: `"\n\nIMPORTANT: Write all text values in {LANGUAGE_NAME}. Keep JSON keys, ticker symbols, numbers, and dates in English."` where LANGUAGE_NAME is a lookup from locale code to full name (e.g., "ko" → "Korean"). Define a `LANGUAGE_NAMES` dict at module level with all 10 supported languages.
- [x] T014 [US3] Inject language instruction into collaborative agent system prompts in `packages/mcp-server/src/agents/collaborative/base.py`. Same approach as T013: in the `run()` method, check `self.settings.output_language` and append the language instruction to the system prompt. Import or duplicate the `LANGUAGE_NAMES` dict.
- [x] T015 [US3] Ensure `output_language` flows from extension to server. In `packages/extension/src/background/service-worker.ts`, the `handleGenerate()` function already passes `user_settings: settings` in the request. Verify that `output_language` is included in the settings object passed to `generateIdeaStream()`. No code change needed if `getSettings()` returns the full object — just verify the field is not stripped anywhere in the chain.

**Checkpoint**: Language selection end-to-end — FR-009 through FR-013 confirmed. Reports generate in selected language.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, RTL support, and final verification

- [x] T016 Add RTL text direction support in `packages/extension/src/sidepanel/index.html`. Add CSS rule: `.rtl { direction: rtl; text-align: right; }`. In `packages/extension/src/sidepanel/panel.ts`, when rendering report sections or chat bubbles, check if the current `output_language` setting is `"ar"` and add `rtl` class to the content containers. Note: Hindi uses LTR Devanagari script, not RTL.
- [x] T017 Add chat error handling with retry in `packages/extension/src/sidepanel/panel.ts`. In the `sendMessage()` catch block, append an error bubble to the chat thread with text "Failed to get response" and a "Retry" button. Clicking Retry re-sends the last user message. Remove the error bubble when retry is clicked.
- [x] T018 Build extension and verify: run `cd packages/extension && npm run build`. Fix any TypeScript compilation errors. Load the built extension in Chrome and run through the 5 quickstart scenarios from `specs/005-panel-chat-language/quickstart.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately. All T001-T003 are [P] parallel.
- **US1 Progress (Phase 2)**: Depends on Phase 1. T004 and T005 are sequential (same file).
- **US2 Chat (Phase 3)**: Depends on Phase 1 (needs ChatMessage type). T006-T007 are [P] parallel (different packages). T008-T010 are sequential (same files).
- **US3 Language (Phase 4)**: Depends on Phase 1 (needs output_language field). T011-T012 are [P] parallel with T013-T014. T015 is verification only.
- **Polish (Phase 5)**: Depends on US1-US3 completion.

### User Story Dependencies

- **US1 (P1)**: Independent. No cross-story dependencies.
- **US2 (P2)**: Independent. Uses ChatMessage type from Phase 1.
- **US3 (P3)**: Independent. Uses output_language from Phase 1. Language also applies to US2 chat responses (T006 handles this via user_settings).

### Parallel Opportunities

```text
Phase 1 (all parallel):
  T001 (server model) || T002 (extension types) || T003 (storage defaults)

Phase 2-4 (stories can run in parallel after Phase 1):
  US1 (T004-T005) || US2 (T006-T010) || US3 (T011-T015)

Within US2:
  T006 (server endpoint) || T007 (api client)  →  then T008 → T009 → T010

Within US3:
  T011 (options html) || T012 (options ts) || T013 (base agent) || T014 (collab agent)
  →  then T015 (verification)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational types
2. Complete Phase 2: Verify progress display
3. **STOP and VALIDATE**: Progress works correctly
4. This is already largely done — low effort MVP

### Incremental Delivery

1. Phase 1 (types) → Phase 2 (US1 progress polish) → Validate
2. Phase 3 (US2 chat) → Validate chat independently
3. Phase 4 (US3 language) → Validate language selection
4. Phase 5 (polish, RTL, error handling) → Final validation

### Notes

- US1 is mostly verification of existing code (lowest effort)
- US2 is the largest effort (new server endpoint + full chat UI)
- US3 is moderate effort (settings UI + prompt injection)
- [P] tasks can run in parallel within their phase
- Commit after each completed phase
