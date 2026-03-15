# Data Model: Thinking Mode Toggle & Display

## Extended Entities

### UserSettings (extended)

Add to existing `UserSettings` in `models/idea_report.py`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| thinking_mode | bool | False | Whether to enable LLM thinking/reasoning mode |

### IdeaRequest (extended)

The `thinking_mode` preference flows from `UserSettings` through `IdeaRequest` to the server. No separate field needed — it's part of `user_settings`.

### GenerationState (extended, client-side)

Add to existing `GenerationState` in `types/index.ts`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| thinking_chunks | ThinkingChunk[] | [] | Accumulated thinking output grouped by agent |

### ThinkingChunk

New entity for streaming thinking tokens:

| Field | Type | Description |
|-------|------|-------------|
| agent_id | string | Originating agent identifier (e.g., "thesis_agent", "news_agent") |
| phase | "sequential" \| "parallel" | Pipeline phase grouping |
| content | string | Accumulated thinking text for this agent |

### IdeaReport (extended)

Add to existing `IdeaReport` for persistence/export:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| thinking_output | dict[str, AgentThinking] \| None | None | Thinking content per agent, keyed by agent_id |

### AgentThinking

| Field | Type | Description |
|-------|------|-------------|
| agent_id | string | Agent identifier |
| phase | "sequential" \| "parallel" | Pipeline phase |
| content | string | Full thinking text |

## State Transitions

### Thinking Stream Lifecycle

```
[idle] → thinking_mode enabled in settings
  ↓
[generation_started] → SSE connection opened
  ↓
[thinking_streaming] → thinking events arrive with agent_id + content
  ↓ (per agent)
[agent_thinking_complete] → agent's thinking section finalized
  ↓ (all agents done)
[report_complete] → thinking collapsed, report displayed
```

## Storage

- **thinking_mode preference**: `chrome.storage.local` alongside existing provider settings
- **thinking_output in reports**: Stored as part of `IdeaReport` in `chrome.storage.local` history
- **thinking_chunks during generation**: In-memory only (GenerationState), not persisted until report completes
