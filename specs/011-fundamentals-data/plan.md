# Implementation Plan: Fundamentals Data Retrieval

**Branch**: `011-fundamentals-data` | **Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-fundamentals-data/spec.md`

## Summary

Enhance the existing FundamentalsAgent to retrieve real financial data (P/E, market cap, dividend yield, 52-week range, EPS) using a priority chain of data sources (yfinance → investpy → scraping). Implement SQLite-based caching with 24-hour TTL to reduce API calls and improve performance.

## Technical Context

**Language/Version**: Python 3.13 (MCP server), TypeScript (Chrome Extension MV3)
**Primary Dependencies**: FastAPI, LiteLLM, Pydantic 2.x, yfinance, investpy, aiosqlite (server); Chrome Extension APIs (client)
**Storage**: SQLite (fundamentals cache), chrome.storage.local (extension settings)
**Testing**: pytest, pytest-asyncio
**Target Platform**: macOS/Linux server, Chrome browser extension
**Project Type**: Web application (backend API + browser extension frontend)
**Performance Goals**: <3s added latency for fresh data fetch, <100ms for cached data
**Constraints**: No paid data APIs, graceful degradation on failures
**Scale/Scope**: Single-user Chrome extension, ~1000 tickers cached over time

## Constitution Check

*No constitution.md found - proceeding without gate checks.*

## Project Structure

### Documentation (this feature)

```text
specs/011-fundamentals-data/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
packages/
├── mcp-server/
│   └── src/
│       ├── agents/
│       │   └── collaborative/
│       │       └── fundamentals.py    # Enhanced with real data sources
│       ├── models/
│       │   └── collaborative.py       # Update FundamentalsSnapshot model
│       ├── providers/
│       │   └── fundamentals/          # NEW: Data provider implementations
│       │       ├── __init__.py
│       │       ├── base.py            # Abstract base provider
│       │       ├── yfinance.py        # Primary: yfinance provider
│       │       ├── investpy.py        # Secondary: investpy provider
│       │       └── scraper.py         # Tertiary: web scraper
│       ├── storage/                   # NEW: SQLite cache layer
│       │   ├── __init__.py
│       │   └── fundamentals_cache.py
│       └── tools/
│           └── ticker_search.py       # Existing, may extend
└── extension/
    └── src/
        └── sidepanel/
            └── panel.ts               # Update to display fundamentals
```

**Structure Decision**: Extend existing monorepo packages structure. Add `providers/fundamentals/` for data source implementations and `storage/` for SQLite cache management.
