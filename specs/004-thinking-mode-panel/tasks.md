# Tasks: Thinking Mode Toggle & Display

**Input**: Design documents from `/specs/004-thinking-mode-panel/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend shared data models and types needed by all user stories

- [x] T001 [P] Add `thinking_mode: bool = False` field to `UserSettings` and `thinking_output: dict | None = None` field to `IdeaReport` in packages/mcp-server/src/models/idea_report.py
- [x] T002 [P] Add `ThinkingChunk` interface and extend `GenerationState` with `thinking_chunks?: ThinkingChunk[]` in packages/extension/src/types/index.ts
- [x] T003 [P] Add `thinking_mode` boolean to settings save/load in packages/extension/src/lib/storage.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core streaming infrastructure — `<think>` tag parser and streaming completion method

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Add `complete_streaming()` method to `LLMProvider` in packages/mcp-server/src/providers/llm.py — uses `acompletion(stream=True)`, parses `<think>...</think>` tags from streaming chunks with a state machine buffer, accepts `on_thinking(content: str)` callback, accepts `thinking_mode: bool` flag (when False for NRP provider, passes `extra_body={"chat_template_kwargs": {"enable_thinking": False}}`), returns final content with `<think>` blocks stripped

**Checkpoint**: Foundation ready — streaming `<think>` parser works, models extended

---

## Phase 3: User Story 1 — Show Thinking Process in Side Panel (Priority: P1)

**Goal**: Stream LLM thinking tokens to the side panel in real-time, grouped by pipeline phase

**Independent Test**: Select text, trigger generation with thinking mode enabled, observe thinking tokens appearing in real-time in the side panel grouped by agent phase before the final report renders

### Implementation for User Story 1

- [x] T005 [US1] Update `Pipeline.run()` to accept `on_thinking` callback alongside `on_stage` and pass `thinking_mode` from `UserSettings` to each sequential agent call in packages/mcp-server/src/agents/pipeline.py — when `thinking_mode=True`, use `complete_streaming()` instead of `complete()` for each sequential agent (extraction, entity, ticker, thesis, critique, confidence), emit thinking via `on_thinking` with `agent_id` and `phase="sequential"`
- [x] T006 [US1] Update `_run_collaborative()` in packages/mcp-server/src/agents/pipeline.py to pass `on_thinking` callback to the Coordinator and to collaborative agent runs
- [x] T007 [US1] Update `Coordinator.coordinate()` and `run_agents_parallel()` in packages/mcp-server/src/agents/collaborative/coordinator.py to accept and forward `on_thinking` callback to each agent's `run()` method
- [x] T008 [US1] Update `CollaborativeAgent.run()` in packages/mcp-server/src/agents/collaborative/base.py to accept `on_thinking` callback and `thinking_mode` flag — when enabled and tools are NOT used, use `complete_streaming()` for the LLM call; when tools ARE used, use existing `complete_with_tools()` but parse `<think>` tags from the first LLM response only (before tool calls begin), emitting thinking tokens with `agent_id` and appropriate `phase` ("parallel" for data agents, "sequential" for risk/synthesis)
- [x] T009 [US1] Update SSE endpoint `/api/v1/ideas/stream` in packages/mcp-server/src/api_server.py to create `on_thinking` callback that pushes `event: thinking` with `{"agent_id", "phase", "content"}` to the async queue, and pass it to `pipeline.run()`
- [x] T010 [US1] Update `generateIdeaStream()` in packages/extension/src/lib/api.ts to accept `onThinking(agentId: string, phase: string, content: string)` callback and handle new `thinking` SSE event type
- [x] T011 [US1] Update service worker `handleGenerate()` in packages/extension/src/background/service-worker.ts to pass `onThinking` callback to `generateIdeaStream()`, accumulate `ThinkingChunk[]` per agent in generation state, and store `thinking_output` with completed report
- [x] T012 [US1] Add `renderThinking()` method to panel in packages/extension/src/sidepanel/panel.ts — groups thinking by phase ("Parallel Analysis" header for parallel agents, individual labels for sequential), each agent gets a collapsible `<details>` section with monospace italic text, auto-scroll that pauses on user scroll-up and resumes when scrolled to bottom, collapse all sections when report completes, use requestAnimationFrame for batched DOM updates to avoid jank with large thinking output (up to 10,000 tokens), and cap displayed thinking at 50,000 characters with a "[Thinking truncated]" notice
- [x] T013 [US1] Add CSS styles for thinking display in packages/extension/src/sidepanel/index.html — `.thinking-section`, `.thinking-agent`, `.thinking-content` with italic monospace muted-color styling, collapsible details elements

**Checkpoint**: Thinking tokens stream from server to panel in real-time, grouped by phase

---

## Phase 4: User Story 2 — Toggle Thinking Mode On/Off (Priority: P2)

**Goal**: Provide settings toggle to enable/disable thinking mode, controlling whether LLM generates reasoning tokens

**Independent Test**: Toggle thinking mode in extension options, generate a report, confirm thinking tokens appear/disappear based on toggle state

### Implementation for User Story 2

- [x] T014 [P] [US2] Add "Thinking Mode" toggle switch to packages/extension/src/options/options.html with label and description text
- [x] T015 [US2] Wire thinking mode toggle in packages/extension/src/options/options.ts — load current `thinking_mode` from storage on page load, save on toggle change, default to false
- [x] T016 [US2] Update service worker in packages/extension/src/background/service-worker.ts to read `thinking_mode` from settings and include it in the `IdeaRequest.user_settings` sent to the API

**Checkpoint**: Users can toggle thinking on/off and see the effect on subsequent generations

---

## Phase 5: User Story 3 — Open Side Panel from Extension UI (Priority: P3)

**Goal**: Add "Open Panel" button to popup so users can access the side panel at any time

**Independent Test**: Click "Open Panel" in popup, verify side panel opens regardless of generation state

### Implementation for User Story 3

- [x] T017 [P] [US3] Add "Open Panel" button markup to packages/extension/src/popup/popup.html — always-visible secondary button
- [x] T018 [US3] Add "Open Panel" click handler in packages/extension/src/popup/popup.ts — calls `chrome.sidePanel.open({ tabId })` for the active tab, wraps in try/catch for graceful error handling

**Checkpoint**: Users can open the side panel from the popup at any time

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Export integration and final validation

- [x] T019 Update Markdown export in packages/extension/src/sidepanel/panel.ts to append thinking output as `<details><summary>Thinking Process</summary>...</details>` block when `thinking_output` is present on the report
- [x] T020 Update JSON export in packages/extension/src/sidepanel/panel.ts to include `thinking_output` field in the exported object
- [x] T021 Build extension (`npm run build` in packages/extension) and validate all changes compile without errors
- [x] T022 Run quickstart.md validation — test all 5 scenarios from specs/004-thinking-mode-panel/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001, T002, T003 can all run in parallel
- **Foundational (Phase 2)**: T004 depends on T001 (needs `thinking_mode` on UserSettings)
- **User Story 1 (Phase 3)**: Depends on T004 (needs `complete_streaming()`)
  - T005 → T006 (sequential: pipeline core then collaborative)
  - T007, T008 depend on T006
  - T009 depends on T005
  - T010 depends on T002 (needs ThinkingChunk type)
  - T011 depends on T010
  - T012 depends on T011
  - T013 can run in parallel with T012
- **User Story 2 (Phase 4)**: Depends on Phase 1 (T003 for storage). Can run in parallel with US1 at file level (T014, T015 touch different files)
- **User Story 3 (Phase 5)**: No dependencies on other stories — can run in parallel
- **Polish (Phase 6)**: Depends on US1 completion (needs thinking_output in report)

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2) — core streaming feature
- **User Story 2 (P2)**: Depends on Setup (Phase 1) — settings toggle only, can run before US1 is complete
- **User Story 3 (P3)**: No dependencies — fully independent, can start after Setup

### Parallel Opportunities

- T001, T002, T003 (all Setup tasks) can run in parallel
- T014 (options HTML) can run in parallel with any Phase 3 task
- T017 (popup HTML) can run in parallel with any other task
- T013 (CSS) can run in parallel with T012 (JS rendering)
- T019, T020 (export updates) can run in parallel

---

## Parallel Example: User Story 1

```bash
# After T004 completes, launch server-side pipeline tasks:
Task: T005 "Update Pipeline.run() in pipeline.py"
# After T005:
Task: T006 "Update _run_collaborative() in pipeline.py"
# After T006, launch in parallel:
Task: T007 "Update Coordinator in coordinator.py"
Task: T008 "Update CollaborativeAgent in base.py"
Task: T009 "Update SSE endpoint in api_server.py"

# Client-side can start after T002:
Task: T010 "Update generateIdeaStream() in api.ts"
# Then sequential:
Task: T011 "Update service worker"
Task: T012 "Add renderThinking() to panel.ts"
Task: T013 "Add CSS styles" (parallel with T012)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003 in parallel)
2. Complete Phase 2: Foundational (T004)
3. Complete Phase 3: User Story 1 (T005-T013)
4. **STOP and VALIDATE**: Test thinking streaming end-to-end
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Thinking streams in panel → Validate (MVP!)
3. Add User Story 2 → Toggle works → Validate
4. Add User Story 3 → Open Panel button works → Validate
5. Polish → Exports include thinking → Final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- The `<think>` tag parser in T004 is the most complex single task — handle partial chunk boundaries carefully
- Service worker changes span US1 (T011) and US2 (T016) — implement T011 first, T016 extends it
- Commit after each phase checkpoint
