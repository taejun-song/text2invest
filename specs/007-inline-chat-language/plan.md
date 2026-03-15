# Implementation Plan: Inline Chat & Language Reliability

**Branch**: `007-inline-chat-language` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)

## Summary

Move the chat UI from a separate tab into the report view (inline, pinned at bottom with collapsible thread) and enforce language consistency in the formatter's executive summary generation.

## Technical Context

**Language/Version**: TypeScript (Chrome Extension MV3), Python 3.13 (MCP server)
**Primary Dependencies**: Chrome Extension APIs, FastAPI, LiteLLM, Pydantic 2.x
**Storage**: chrome.storage.local
**Testing**: Manual verification via Chrome extension reload
**Target Platform**: Chrome browser extension + Python API server
**Project Type**: Monorepo (packages/extension + packages/mcp-server)

## Project Structure

### Source Code Changes

```text
packages/extension/src/sidepanel/
├── index.html          # Remove Chat tab, embed chat into report-view
└── panel.ts            # Remove tabChatBtn, inline chat logic in report view

packages/mcp-server/src/agents/
└── formatter.py        # Language-aware executive summary labels
```

## Changes

### US1: Inline Chat

1. **index.html**: Remove `<button id="tab-chat">` from tabs div. Remove standalone `<div id="chat-view">`. The chat input bar and message thread will be rendered dynamically by panel.ts inside the report view.

2. **panel.ts**:
   - Remove `chatViewEl`, `tabChatBtn` properties and all references
   - Revert `showTab()` to only handle `'report' | 'history'` (no 'chat' tab)
   - In `renderReport()`: append a chat container (collapsible thread + pinned input bar) after the report content
   - Move `initChat()` call into report rendering flow
   - Add collapse/expand toggle for the chat thread
   - Keep all existing chat methods: `sendMessage()`, `appendChatBubble()`, `showTypingIndicator()`, `buildReportContext()`, error retry

3. **CSS in index.html**: Update `.chat-view` to be a flex container within report, add `.chat-toggle` button style, set `.chat-messages` max-height to 40vh with overflow scroll.

### US2: Language Reliability

1. **formatter.py**: Make `_generate_executive_summary()` language-aware. Replace hardcoded "Tickers:" and "Confidence:" labels with a lookup from the LANGUAGE_NAMES equivalent. Use the `output_language` from `self.settings`.
