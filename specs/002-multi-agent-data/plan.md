# Implementation Plan: Multi-Agent Collaborative Investment Analysis

**Branch**: `002-multi-agent-data` | **Date**: 2026-03-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-multi-agent-data/spec.md`

## Summary

This feature evolves Text2Invest from a linear agent pipeline into a multi-agent collaborative system. Specialized agents (News, Fundamentals, Risk, Macro) analyze different data dimensions using Qwen3's tool-calling capability with web search, communicate findings via an in-memory message bus, and a Synthesis Agent combines all perspectives into a single enriched report. The NRP.ai managed LLM service is the sole provider.

**Technical Approach**: Extend the existing Python MCP server with a new `CollaborativeAgent` base class that supports LLM tool calling and message bus interaction. Add `duckduckgo-search` for web search tool functions. Extend `IdeaReport` with optional enrichment fields. Add NRP.ai as a new provider type. Extend the Chrome Extension UI to display enrichment sections and agent communication logs.

## Technical Context

**Language/Version**: Python 3.13 (MCP server), TypeScript (Chrome Extension)
**Primary Dependencies**: FastMCP 2.x, LiteLLM, Pydantic 2.x, duckduckgo-search (server); Chrome Extension APIs (client)
**Storage**: chrome.storage.local (extension), in-memory (server)
**Testing**: pytest (server)
**Target Platform**: Chrome/Edge browsers (MV3), localhost MCP server
**Project Type**: Monorepo with packages (extension + server + shared schemas)
**Performance Goals**: <60s enriched analysis, <5s graceful degradation to text-only
**Constraints**: NRP.ai only (no fallback), local-first storage, no external API subscriptions
**Scale/Scope**: Single user, hundreds of reports locally

## Constitution Check

*No constitution file found. Proceeding with default best practices.*

| Principle | Status | Notes |
|-----------|--------|-------|
| Simplicity | PASS | Extends existing patterns; CollaborativeAgent reuses BaseAgent structure |
| Privacy-first | PASS | Only derived identifiers (tickers, company names) sent to web search; user text never exposed |
| Schema validation | PASS | Pydantic enforces all agent output models and enriched report schema |

## Project Structure

### Documentation (this feature)

```text
specs/002-multi-agent-data/
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
├── core/                          # Shared schemas (existing)
│   └── src/schemas/
│       ├── idea-report.json       # Extended with enrichment fields
│       ├── news-item.json         # New
│       ├── fundamentals-snapshot.json  # New
│       ├── cross-reference.json   # New
│       ├── macro-context.json     # New
│       ├── agent-message.json     # New
│       ├── communication-log.json # New
│       └── agent-config.json      # New
│
├── mcp-server/                    # Python FastMCP server
│   ├── src/
│   │   ├── server.py              # Extended: enriched report in /api/v1/ideas response
│   │   ├── agents/
│   │   │   ├── base.py            # Existing (unchanged)
│   │   │   ├── extraction.py      # Existing (unchanged)
│   │   │   ├── entity.py          # Existing (unchanged)
│   │   │   ├── ticker.py          # Existing (unchanged)
│   │   │   ├── thesis.py          # Existing (unchanged)
│   │   │   ├── critique.py        # Existing (unchanged)
│   │   │   ├── confidence.py      # Existing (unchanged)
│   │   │   ├── formatter.py       # Extended: merge enrichment into IdeaReport
│   │   │   ├── pipeline.py        # Extended: invoke collaborative agents after text pipeline
│   │   │   └── collaborative/     # New: multi-agent subsystem
│   │   │       ├── base.py        # CollaborativeAgent with tool calling + message bus
│   │   │       ├── coordinator.py # Orchestration, message routing, round enforcement
│   │   │       ├── news.py        # News Agent
│   │   │       ├── fundamentals.py # Fundamentals Agent
│   │   │       ├── risk.py        # Risk Agent (cross-referencing)
│   │   │       ├── macro.py       # Macro Agent
│   │   │       └── synthesis.py   # Synthesis Agent
│   │   ├── tools/
│   │   │   ├── generate_idea.py   # Existing (unchanged)
│   │   │   ├── cancellation.py    # Existing (unchanged)
│   │   │   └── web_search.py      # New: DuckDuckGo web search tool functions
│   │   ├── models/
│   │   │   ├── idea_report.py     # Extended: optional enrichment fields, NRP provider
│   │   │   ├── agent_outputs.py   # Existing (unchanged)
│   │   │   └── collaborative.py   # New: NewsItem, FundamentalsSnapshot, AgentMessage, etc.
│   │   └── providers/
│   │       └── llm.py             # Extended: tool calling support, NRP provider routing
│   └── tests/
│       ├── unit/
│       │   ├── test_collaborative_agents.py  # New
│       │   ├── test_coordinator.py           # New
│       │   ├── test_web_search.py            # New
│       │   └── test_tool_calling.py          # New
│       └── integration/
│           └── test_enriched_pipeline.py     # New
│
└── extension/                     # Chrome Extension (MV3)
    └── src/
        ├── sidepanel/
        │   └── panel.ts           # Extended: enrichment sections, agent log viewer
        ├── options/
        │   └── options.ts         # Extended: NRP.ai provider, agent config toggles
        ├── lib/
        │   ├── storage.ts         # Extended: agent config storage
        │   └── export.ts          # Extended: enrichment sections in exports
        └── types/
            └── enriched.ts        # New: TypeScript types for enrichment entities
```

**Structure Decision**: Extends the existing monorepo. All existing linear pipeline code is unchanged. New collaborative agents live in a `collaborative/` subdirectory under `agents/`. New models in a separate `collaborative.py` file. This isolation allows the existing pipeline to function independently if the collaborative subsystem fails.

## Complexity Tracking

No violations to justify. Architecture extends existing patterns with minimal new abstractions.
