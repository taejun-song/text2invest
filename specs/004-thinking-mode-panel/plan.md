# Implementation Plan: Thinking Mode Toggle & Display

**Branch**: `004-thinking-mode-panel` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-thinking-mode-panel/spec.md`

## Summary

Add LLM thinking/reasoning token streaming to the side panel, a toggle to enable/disable thinking mode, and an "Open Panel" button in the popup. Qwen3 models embed thinking in `<think>...</think>` tags within streamed content. The server parses these tags and emits `thinking` SSE events. The extension displays thinking grouped by pipeline phase (parallel agents together, sequential agents in order). Thinking mode defaults to disabled; users opt in via settings.

## Technical Context

**Language/Version**: Python 3.13 (server), TypeScript (extension)
**Primary Dependencies**: LiteLLM, FastAPI, Pydantic 2.x (server); Chrome Extension APIs MV3 (client)
**Storage**: chrome.storage.local (extension settings + report history)
**Testing**: Manual testing via Chrome extension + curl for SSE
**Target Platform**: Chrome browser + Python API server
**Project Type**: Monorepo (packages/mcp-server + packages/extension)
**Performance Goals**: First thinking token visible within 2s; no jank up to 10,000 tokens
**Constraints**: SSE unidirectional streaming; `<think>` tag parsing must handle partial chunks
**Scale/Scope**: Single user, local server

## Constitution Check

No constitution file exists. No gates to evaluate.

## Project Structure

### Documentation (this feature)

```text
specs/004-thinking-mode-panel/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── sse-thinking-events.md
└── tasks.md
```

### Source Code (repository root)

```text
packages/mcp-server/src/
├── api_server.py              # SSE endpoint — add thinking event emission
├── providers/llm.py           # Add streaming completion with <think> tag parsing
├── agents/pipeline.py         # Pass thinking_mode + on_thinking callback through pipeline
├── agents/collaborative/
│   ├── coordinator.py         # Pass on_thinking to agent runs
│   └── base.py                # Emit thinking tokens from agent LLM calls
└── models/idea_report.py      # Add thinking_mode to UserSettings, thinking_output to IdeaReport

packages/extension/src/
├── background/service-worker.ts  # Handle thinking events from SSE, store thinking chunks
├── sidepanel/
│   ├── panel.ts               # Render thinking sections grouped by phase
│   └── index.html             # CSS for thinking display
├── popup/popup.ts             # Add "Open Panel" button handler
├── popup/popup.html           # Add "Open Panel" button markup
├── options/options.ts         # Add thinking mode toggle
├── options/options.html       # Add thinking mode toggle markup
├── lib/api.ts                 # Parse thinking SSE events in stream handler
├── lib/storage.ts             # Persist thinking_mode preference
└── types/index.ts             # Extend GenerationState, add ThinkingChunk type
```

**Structure Decision**: Existing monorepo structure. Changes span both packages — server-side streaming enhancement and client-side display/settings.

## Architecture

### Server-Side: Streaming Thinking Tokens

1. **LLM Provider** (`providers/llm.py`):
   - Add `complete_streaming()` method that uses `acompletion(stream=True)`
   - Parse `<think>...</think>` tags from streaming chunks
   - Accept `on_thinking` callback to emit thinking tokens
   - Accept `thinking_mode` flag; when disabled, pass `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` for NRP/Qwen3 provider
   - Return final content with `<think>` blocks stripped

2. **Pipeline** (`agents/pipeline.py`):
   - Accept `on_thinking` callback alongside existing `on_stage`
   - Pass `thinking_mode` from `UserSettings` to each agent
   - Forward thinking tokens with agent identification

3. **Sequential Agents** (thesis, critique, etc.):
   - When `thinking_mode=True`, use streaming completion
   - Emit thinking tokens via callback with `agent_id` and `phase="sequential"`

4. **Collaborative Agents** (`agents/collaborative/`):
   - Coordinator passes `on_thinking` to each agent's `run()`
   - Parallel agents emit thinking with `phase="parallel"`
   - Sequential agents (risk, synthesis) emit with `phase="sequential"`
   - For agents using tools (`complete_with_tools`): parse `<think>` tags from the first LLM response in the agentic loop only; subsequent tool-result iterations do not produce new thinking

5. **API Server** (`api_server.py`):
   - In SSE endpoint, create `on_thinking` callback that pushes `event: thinking` to the queue
   - Include `agent_id`, `phase`, and `content` in thinking event data

### Client-Side: Display & Settings

1. **SSE Parser** (`lib/api.ts`):
   - Handle new `thinking` event type alongside existing `stage`/`complete`/`error`
   - Accept `onThinking` callback in `generateIdeaStream()`

2. **Service Worker** (`service-worker.ts`):
   - Accumulate thinking chunks per agent in `GenerationState.thinking_chunks`
   - Store thinking output with completed report

3. **Side Panel** (`panel.ts`):
   - New `renderThinking()` method
   - Group thinking by phase: "Parallel Analysis" header for parallel agents, individual labels for sequential
   - Each agent gets a collapsible section with monospace italic text
   - Auto-scroll with pause-on-user-scroll behavior
   - Collapse all thinking sections when report completes

4. **Popup** (`popup.ts` + `popup.html`):
   - Add "Open Panel" button that calls `chrome.sidePanel.open({ tabId })`
   - Button always visible, works regardless of generation state

5. **Options** (`options.ts` + `options.html`):
   - Add "Thinking Mode" toggle switch
   - Persist to `chrome.storage.local` as part of settings
   - Default: false (disabled)

6. **Export** (`panel.ts` export functions):
   - Markdown: Append `<details><summary>Thinking Process</summary>...</details>` block
   - JSON: Include `thinking_output` field in exported object

### `<think>` Tag Parsing Strategy

LLM streaming returns content in chunks that may split `<think>` tags across chunk boundaries:

```
chunk1: "Let me analyze <thi"
chunk2: "nk>This is my reasoning"
chunk3: "</think>The answer is..."
```

Strategy:
- Maintain a buffer per LLM call
- Track state: `outside_think` or `inside_think`
- When `<think>` tag detected → switch to `inside_think`, emit content via `on_thinking`
- When `</think>` tag detected → switch to `outside_think`, resume content accumulation
- Handle partial tags at chunk boundaries by buffering until tag completes

## Complexity Tracking

No constitution violations to track.
