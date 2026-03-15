# Implementation Plan: Panel Chat & Language Selection

**Branch**: `005-panel-chat-language` | **Date**: 2026-03-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-panel-chat-language/spec.md`

## Summary

Add three features to the Chrome extension: (1) enhanced real-time progress display in the side panel with stage checklists and elapsed timer, (2) a chat interface for asking follow-up questions about generated reports, and (3) output language selection so reports and chat responses can be produced in the user's native language.

## Technical Context

**Language/Version**: Python 3.13 (MCP server), TypeScript (Chrome Extension MV3)
**Primary Dependencies**: FastAPI, LiteLLM, Pydantic 2.x (server); Chrome Extension APIs, Vite (client)
**Storage**: `chrome.storage.local` (extension settings, reports), in-memory (server)
**Testing**: Manual integration testing via browser
**Target Platform**: Chrome browser extension + Python API server (localhost:8000)
**Project Type**: Multi-package (extension + server)
**Performance Goals**: Progress updates within 2s, chat responses within 15s
**Constraints**: Chat context is ephemeral (in-memory only), language selection persists via chrome.storage

## Constitution Check

No constitution file exists. No gates to evaluate.

## Project Structure

### Documentation (this feature)

```text
specs/005-panel-chat-language/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── chat-api.md      # Chat endpoint contract
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
packages/
├── mcp-server/
│   └── src/
│       ├── api_server.py              # Add /api/v1/chat endpoint
│       ├── models/
│       │   └── idea_report.py         # Add output_language to UserSettings
│       ├── agents/
│       │   ├── base.py                # Inject language instruction into system prompts
│       │   ├── pipeline.py            # Pass language through pipeline
│       │   └── collaborative/
│       │       └── base.py            # Inject language for collaborative agents
│       └── providers/
│           └── llm.py                 # No changes needed
│
└── extension/
    └── src/
        ├── types/
        │   └── index.ts               # Add ChatMessage, output_language to UserSettings
        ├── lib/
        │   ├── api.ts                 # Add chatWithReport() function
        │   └── storage.ts             # Add output_language to DEFAULT_SETTINGS
        ├── sidepanel/
        │   ├── index.html             # Add Chat tab, chat UI markup, chat CSS
        │   └── panel.ts              # Add ChatController, Chat tab logic, progress enhancements
        └── options/
            ├── index.html             # Add language dropdown to settings form
            └── options.ts             # Handle language selection save/load
```

**Structure Decision**: Existing multi-package monorepo. Changes span both packages. No new packages needed.

## Complexity Tracking

No constitution violations. No complexity justifications needed.
