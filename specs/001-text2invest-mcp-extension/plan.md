# Implementation Plan: Text2Invest

**Branch**: `001-text2invest-mcp-extension` | **Date**: 2026-02-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-text2invest-mcp-extension/spec.md`

## Summary

Text2Invest is a browser extension + MCP server system that converts user-selected text into structured, uncertainty-aware investment ideas. The extension detects text selection, sends it to a local MCP server, which orchestrates a multi-stage AI agent pipeline to produce a validated IdeaReport. Users can view reports in a side panel, search history, export to Markdown/JSON, and rate results.

**Technical Approach**: Python 3.13 FastMCP server with LiteLLM provider abstraction, Chrome Extension (MV3) with TypeScript, Pydantic for schema validation, and chrome.storage.local for persistence.

## Technical Context

**Language/Version**: Python 3.13 (MCP server), TypeScript (browser extension)
**Primary Dependencies**: FastMCP 2.x, LiteLLM, Pydantic 2.x (server); Chrome Extension APIs (client)
**Storage**: chrome.storage.local (extension), in-memory with file cache (server)
**Testing**: pytest (server), Playwright (extension E2E)
**Target Platform**: Chrome/Edge browsers (MV3), localhost MCP server
**Project Type**: Monorepo with packages (extension + server + shared schemas)
**Performance Goals**: <30s end-to-end generation, <1s UI response
**Constraints**: Local-first, no external storage, minimal permissions
**Scale/Scope**: Single user, hundreds of reports locally

## Constitution Check

*No constitution file found. Proceeding with default best practices.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Simplicity | PASS | Minimal abstractions, direct communication |
| Privacy-first | PASS | All data local, user-provided API keys only |
| Schema validation | PASS | Pydantic enforces frozen schema |

## Project Structure

### Documentation (this feature)

```text
specs/001-text2invest-mcp-extension/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI spec)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
packages/
├── core/                    # Shared schemas and types
│   ├── src/
│   │   ├── schemas/         # IdeaReport, Ticker, etc. (JSON Schema)
│   │   └── validators/      # Schema validation utilities
│   └── package.json
│
├── mcp-server/              # Python FastMCP server
│   ├── src/
│   │   ├── server.py        # FastMCP server entry point
│   │   ├── agents/          # Multi-stage agent pipeline
│   │   │   ├── extraction.py
│   │   │   ├── entity.py
│   │   │   ├── ticker.py
│   │   │   ├── thesis.py
│   │   │   ├── critique.py
│   │   │   ├── confidence.py
│   │   │   └── formatter.py
│   │   ├── providers/       # LLM provider abstraction
│   │   │   └── llm.py       # LiteLLM wrapper
│   │   └── tools/           # MCP tool definitions
│   │       └── generate_idea.py
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   └── pyproject.toml
│
└── extension/               # Chrome Extension (MV3)
    ├── src/
    │   ├── manifest.json    # MV3 manifest
    │   ├── content/         # Content script (selection detection)
    │   │   └── selection.ts
    │   ├── background/      # Service worker (MCP communication)
    │   │   └── service-worker.ts
    │   ├── sidepanel/       # Side panel UI (report viewer)
    │   │   ├── index.html
    │   │   └── panel.ts
    │   ├── popup/           # Selection popup UI
    │   │   ├── index.html
    │   │   └── popup.ts
    │   ├── options/         # Settings page
    │   │   ├── index.html
    │   │   └── options.ts
    │   ├── lib/             # Shared utilities
    │   │   ├── storage.ts   # chrome.storage.local wrapper
    │   │   ├── api.ts       # MCP server communication
    │   │   └── export.ts    # Markdown/JSON export
    │   └── types/           # TypeScript types (generated from core)
    ├── tests/
    │   └── e2e/
    ├── package.json
    └── tsconfig.json

tests/
├── contract/                # Schema contract tests
└── e2e/                     # Full integration tests
```

**Structure Decision**: Monorepo with three packages: `core` (shared schemas), `mcp-server` (Python), and `extension` (TypeScript). This enables schema sharing and independent development/testing of each component.

## Complexity Tracking

No violations to justify. Architecture uses minimal components.
