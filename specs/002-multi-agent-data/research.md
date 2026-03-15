# Research: Multi-Agent Collaborative Investment Analysis

**Date**: 2026-03-15
**Source**: [spec.md](./spec.md)

## Research Topics

### 1. LLM Tool Calling via LiteLLM

**Decision**: Use LiteLLM's built-in tool calling support with OpenAI-compatible format.

**Rationale**: LiteLLM natively supports the `tools` parameter in `acompletion()`, handling tool call loops across all providers. The NRP.ai endpoint is OpenAI-compatible, so tool calling works with the `openai/` model prefix + custom `api_base`. No additional abstraction layer needed.

**Alternatives considered**:
- Direct OpenAI SDK calls: Rejected — would bypass LiteLLM's provider abstraction
- LangChain tool use: Rejected — unnecessary dependency, LiteLLM handles this natively

**Key technical details**:
- Tools passed as OpenAI-format dicts with `type: "function"` and JSON Schema parameters
- Response includes `tool_calls` array when model requests tool execution
- Tool results sent back as `role: "tool"` messages with matching `tool_call_id`
- Loop continues until model returns text response (no more tool calls)

### 2. Web Search Implementation

**Decision**: Use `duckduckgo-search` Python package for web search tool functions.

**Rationale**: Free, no API key required, aligns with spec requirement of "no custom API subscriptions." Returns structured results with titles, URLs, and snippets. Supports news search and regular web search via separate methods.

**Alternatives considered**:
- SearXNG (self-hosted): Rejected — requires deploying a separate service
- Tavily: Rejected — requires paid API key
- SerpAPI: Rejected — requires paid API key
- Direct scraping: Rejected — fragile, rate-limited, legal concerns

**Key technical details**:
- `DDGS().text(query, max_results=5)` for general web search
- `DDGS().news(query, max_results=5)` for news-specific search
- Returns list of dicts with `title`, `href`, `body` fields
- Rate limiting may apply; implement backoff

### 3. NRP.ai Provider Integration

**Decision**: Add `NRP` as a new `Provider` enum value that routes through LiteLLM's OpenAI-compatible pathway with the real API key.

**Rationale**: The existing OpenAI custom endpoint path sets `api_key = "not-needed"` for custom base URLs. NRP.ai requires a real bearer token. Adding a dedicated provider type is cleaner than special-casing OpenAI behavior.

**Alternatives considered**:
- Reuse OpenAI provider with custom base_url: Rejected — existing code sets dummy API key for custom endpoints, which breaks NRP.ai authentication
- Hardcode NRP.ai config: Rejected — user should configure via settings UI

**Key technical details**:
- Base URL: `https://ellm.nrp-nautilus.io/v1`
- Model name: `qwen3` (maps to Qwen3.5-397B-A17B-FP8)
- Auth: Bearer token via `api_key` parameter
- LiteLLM model string: `openai/qwen3` with `api_base` set to NRP.ai URL
- 1M context window, multimodal, tool calling supported

### 4. Multi-Agent Coordination Pattern

**Decision**: In-memory message bus with a Coordinator class that manages agent lifecycle, message routing, and round enforcement.

**Rationale**: Single-user server-side execution means no need for distributed message queues. Simple Python data structures (list of AgentMessage) provide full functionality. The Coordinator orchestrates: (1) parallel agent launch, (2) message exchange rounds, (3) round limit enforcement, (4) synthesis trigger.

**Alternatives considered**:
- Redis pub/sub: Rejected — overkill for single-user, adds infrastructure dependency
- asyncio.Queue per agent: Rejected — complicates coordination; a shared list with coordinator control is simpler
- LangGraph: Rejected — heavy dependency, opinionated workflow graph not needed for 3-round limit

**Key technical details**:
- Coordinator holds `messages: list[AgentMessage]` as the shared bus
- Agents receive relevant messages filtered by recipient before each round
- Round flow: all agents run in parallel → collect outputs → distribute messages → repeat (max 3 rounds)
- After rounds complete, Coordinator invokes Synthesis Agent with all accumulated findings

### 5. Collaborative Agent Design

**Decision**: New `CollaborativeAgent` base class extending the existing `BaseAgent` with tool calling support and message bus integration.

**Rationale**: Preserves the existing agent pattern (abstract methods for prompts + output model) while adding: (1) tool definitions, (2) tool execution loop, (3) message sending/receiving. The existing linear pipeline agents remain unchanged.

**Alternatives considered**:
- Modify existing BaseAgent: Rejected — would affect the working linear pipeline
- Standalone agent classes: Rejected — would duplicate retry logic and LLM interaction code

**Key technical details**:
- `CollaborativeAgent` adds `get_tools()` abstract method returning tool definitions
- `run()` override handles the tool call loop (call LLM → execute tools → send results back → repeat)
- `send_message()` and `receive_messages()` methods for message bus interaction
- Each agent has an `agent_id` for message routing

### 6. Report Schema Extension

**Decision**: Extend `IdeaReport` with optional enrichment fields rather than creating a separate model.

**Rationale**: Per clarification, the system produces a single unified report. Making enrichment fields optional (`| None`) means the same model works for both text-only and enriched reports. No separate storage or query logic needed.

**Alternatives considered**:
- Separate EnrichedReport model: Rejected — creates two report types in storage, complicates history/search
- Composition (IdeaReport + EnrichmentData): Considered viable but adds indirection; optional fields are simpler

**Key technical details**:
- Add optional fields to IdeaReport: `news_context`, `fundamentals_summary`, `cross_reference_analysis`, `macro_context`, `agent_attributions`, `communication_log`
- When data agents are disabled/fail, these fields are `None`
- Extension UI conditionally renders sections based on field presence
