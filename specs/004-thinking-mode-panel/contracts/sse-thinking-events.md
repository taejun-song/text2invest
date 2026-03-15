# SSE Contract: Thinking Events

Extends the existing SSE protocol at `POST /api/v1/ideas/stream`.

## New Event Type: `thinking`

```
event: thinking
data: {"agent_id": "thesis_agent", "phase": "sequential", "content": "Let me analyze the investment thesis..."}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| agent_id | string | yes | Which agent produced this thinking chunk |
| phase | "sequential" \| "parallel" | yes | Pipeline phase for UI grouping |
| content | string | yes | Thinking text chunk (incremental, not cumulative) |

### Event Ordering

Thinking events are interleaved with existing stage events:

```
event: stage
data: {"stage": "extraction"}

event: thinking
data: {"agent_id": "extraction_agent", "phase": "sequential", "content": "I need to extract..."}

event: stage
data: {"stage": "entity"}

event: thinking
data: {"agent_id": "entity_agent", "phase": "sequential", "content": "Looking for companies..."}

...

event: stage
data: {"stage": "enrichment:news_agent,fundamentals_agent,macro_agent"}

event: thinking
data: {"agent_id": "news_agent", "phase": "parallel", "content": "Searching for recent news..."}

event: thinking
data: {"agent_id": "fundamentals_agent", "phase": "parallel", "content": "Analyzing financial data..."}

event: stage
data: {"stage": "agent_done:news_agent"}

event: thinking
data: {"agent_id": "risk_agent", "phase": "sequential", "content": "Evaluating risks based on..."}

event: stage
data: {"stage": "formatting"}

event: complete
data: {IdeaReport JSON with thinking_output field}
```

### Behavior When Thinking Mode Disabled

No `thinking` events are emitted. The SSE stream behaves identically to the current implementation.

## Extended Request Body

The existing `IdeaRequest` carries `user_settings.thinking_mode: bool`. No new endpoint or request field needed.

## Extended Response: IdeaReport

When thinking mode is enabled and thinking was produced, `IdeaReport` includes:

```json
{
  "thinking_output": {
    "thesis_agent": {
      "agent_id": "thesis_agent",
      "phase": "sequential",
      "content": "Full thinking text..."
    },
    "news_agent": {
      "agent_id": "news_agent",
      "phase": "parallel",
      "content": "Full thinking text..."
    }
  }
}
```

When thinking mode is disabled or no thinking tokens produced: `"thinking_output": null`.
