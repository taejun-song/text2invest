# Research: Inline Chat & Language Reliability

## R1: Inline Chat Placement

**Decision**: Embed chat as a collapsible section at the bottom of the report view, with the input bar pinned at the very bottom.
**Rationale**: Keeps report content and chat in the same scrollable view. Collapsible thread prevents chat from dominating the viewport.
**Alternatives**: Floating chat overlay (rejected — blocks report content), split pane (rejected — side panel too narrow).

## R2: Chat Thread Max Height

**Decision**: Cap chat thread at 40% viewport height with its own scrollbar.
**Rationale**: Ensures at least 60% of the viewport remains for report content even when chat is expanded.

## R3: Language-Aware Executive Summary

**Decision**: Use a simple label translation lookup in the formatter rather than an LLM call.
**Rationale**: The executive summary only has two hardcoded English labels ("Tickers:" and "Confidence:"). A lookup table is faster and deterministic. The thesis text already comes from the LLM in the target language.
**Alternatives**: LLM post-processing (rejected — adds latency for 2 labels).

## R4: Chat Tab Removal

**Decision**: Completely remove the Chat tab and all tab-switching logic for chat. The chat is only accessible within the report view.
**Rationale**: Reduces tab clutter from 3 to 2 tabs. Chat is contextually tied to a report, so it belongs in the report view.
