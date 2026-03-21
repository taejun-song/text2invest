# Research: Panel Chat & Language Selection

**Feature**: 005-panel-chat-language
**Date**: 2026-03-15

## R1: Chat Architecture for Report Q&A

**Decision**: Server-side chat endpoint (`POST /api/v1/chat`) that receives the full report context + chat history + user message, and returns an LLM-generated response.

**Rationale**: The extension already sends `UserSettings` (with provider/model/API key) to the server for report generation. Reusing the same LLM provider via a new server endpoint keeps the architecture consistent and avoids exposing API keys in client-side chat calls.

**Alternatives considered**:
- Client-side direct LLM calls: Would require embedding API keys in extension context, inconsistent with existing pattern.
- WebSocket-based chat: Over-engineered for single request/response pattern. SSE not needed since chat responses are short enough to wait for.
- Streaming chat responses: Adds complexity. Given 15s target and short responses, a simple POST/response is sufficient for MVP.

## R2: Language Injection Strategy

**Decision**: Inject a language instruction into the system prompt of each agent that produces user-facing text. The instruction is appended to the existing system prompt: `"IMPORTANT: You MUST write all your output text in {language}. Keep ticker symbols, numbers, dates, and JSON keys in English."`.

**Rationale**: LLMs respond well to explicit language instructions in system prompts. This approach requires minimal code changes (add instruction in `BaseAgent.run()` and `CollaborativeAgent.run()` based on `settings.output_language`), preserves existing agent logic, and naturally handles the requirement that structured data (tickers, numbers) stays in English because the JSON schema keys remain unchanged.

**Alternatives considered**:
- Post-processing translation: Adds latency, loses nuance, requires separate translation API.
- Separate language-specific prompts per agent: Massive duplication, hard to maintain.
- LiteLLM language parameter: No such parameter exists; language must be controlled via prompts.

## R3: Chat Context Window Management

**Decision**: Send a system message containing the full report summary (thesis, tickers, risks, confidence, enrichment summaries) plus the last 10 chat messages as conversation history. Truncate report context to 4000 characters if needed.

**Rationale**: Reports are typically 2-3KB of text. With a 4K char cap on context and 10 messages of history, the total prompt stays well within the model's context window. The 10-message limit prevents context bloat in long conversations.

**Alternatives considered**:
- Send full raw report JSON: Too large, wastes tokens on structural data.
- Embeddings/RAG: Over-engineered for a single-report context.
- No message limit: Could exceed context window in extended conversations.

## R4: Language Dropdown UX

**Decision**: Add a `<select>` dropdown in the extension settings page (options.html) with 10 predefined languages. Store as a locale code string (e.g., "en", "ko") in `UserSettings.output_language`. Default: "en".

**Rationale**: A simple dropdown is consistent with the existing settings page style. Locale codes are standard and compact for storage. 10 languages covers the most common needs per the spec.

**Alternatives considered**:
- Searchable autocomplete: Over-engineered for 10 options.
- Browser locale auto-detection: User may want a different language than their browser locale.
- Per-report language selection: Out of scope per spec; language is a global preference.

## R5: Progress Display Enhancement

**Decision**: The existing progress view in `panel.ts` already implements most of FR-001 through FR-004 (stage checklist with spinners, checkmarks, agent result previews, elapsed timer, auto-transition). Only minor refinements needed: ensure the timer shows mm:ss format and verify all stages render correctly.

**Rationale**: The previous session (004-thinking-mode-panel) already built the progress infrastructure including `renderProgress()`, stage lists, agent result previews, and elapsed timer. The spec's P1 requirements are largely met by existing code.

**Alternatives considered**: N/A — existing implementation satisfies requirements.
