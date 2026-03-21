# Research: Thinking Mode Toggle & Display

## R1: How to stream thinking tokens from Qwen3 via LiteLLM

**Decision**: Parse `<think>...</think>` tags from streamed content rather than relying on LiteLLM's `reasoning_content` field.

**Rationale**: LiteLLM's `reasoning_content` field is unreliable in streaming mode (multiple open GitHub issues: #15233, #20246, #7942). Qwen3 models served via vLLM embed thinking in content as `<think>...</think>` tags. Parsing these tags from the streaming response is the most reliable approach.

**Alternatives considered**:
- Use `reasoning_content` field from LiteLLM streaming chunks → Unreliable, often `None`
- Use non-streaming mode and extract `reasoning_content` after completion → Works but defeats the purpose of real-time streaming
- Use `thinking_blocks` (Anthropic-specific) → Only works for Anthropic models, not Qwen3

## R2: How to toggle thinking mode on/off for Qwen3

**Decision**: Use `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` in LiteLLM's `acompletion()` call to disable thinking. Omit the parameter (or set `True`) to enable thinking.

**Rationale**: Qwen3/Qwen3.5 models served via vLLM have thinking enabled by default. The `chat_template_kwargs` parameter is the official vLLM mechanism to control this per-request. LiteLLM passes `extra_body` through to the underlying API.

**Alternatives considered**:
- Use `reasoning_effort` parameter → Not supported by Qwen3/vLLM
- Server-side vLLM config to disable globally → Removes per-user control
- Prompt-based suppression ("Do not think") → Unreliable

## R3: Streaming architecture for thinking tokens

**Decision**: Extend the existing SSE streaming to emit `thinking` events alongside `stage` events. The server parses `<think>` tags from LLM streaming responses and forwards thinking chunks as separate SSE events with agent identification.

**Rationale**: The existing SSE infrastructure (asyncio.Queue + StreamingResponse) can be extended to carry a new event type. This keeps the protocol simple and avoids breaking the existing stage-based progress tracking.

**Alternatives considered**:
- WebSocket for bidirectional streaming → Overkill for unidirectional token streaming; adds complexity
- Separate endpoint for thinking stream → Requires managing two concurrent connections per generation
- Batch thinking after each agent completes → Loses real-time streaming benefit

## R4: Provider compatibility for thinking toggle

**Decision**: Only pass `enable_thinking` for providers that support it (NRP/Qwen3 via vLLM). For other providers, ignore the thinking mode setting and skip thinking display. No error shown to user.

**Rationale**: Different LLM providers have different thinking mechanisms (Anthropic uses `thinking` parameter, OpenAI doesn't support it, Ollama depends on model). Graceful fallback is safer than attempting provider-specific implementations for all.

**Alternatives considered**:
- Implement per-provider thinking toggle (Anthropic `thinking`, OpenAI reasoning, etc.) → Scope creep, each provider has different semantics
- Show error when provider doesn't support thinking → Poor UX for a preference toggle
