# Implementation Plan: Smart Ticker Discovery

**Branch**: `009-smart-ticker-discovery` | **Date**: 2026-03-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-smart-ticker-discovery/spec.md`

## Summary

Extend the existing TickerAgent to perform sector-aware inference of relevant companies even when no companies are explicitly mentioned in the text. The agent will identify sectors/themes from the text, infer related publicly traded companies, and return them with confidence levels and relevance explanations — all while maintaining the current pipeline flow with minimal latency impact.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastMCP 2.x, LiteLLM, Pydantic 2.x, yfinance, rapidfuzz
**Storage**: N/A (in-memory processing only)
**Testing**: pytest, pytest-asyncio
**Target Platform**: MCP server (macOS/Linux), Chrome Extension MV3 (client)
**Project Type**: Multi-package (packages/mcp-server + packages/extension)
**Performance Goals**: Sector inference adds ≤30% to total pipeline time (SC-004)
**Constraints**: Single LLM call for sector+inference to minimize latency; yfinance for verification
**Scale/Scope**: Real-time analysis of user-selected text (single request pattern)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution.md file found in `.specify/memory/`. Proceeding without constitution gates.

## Project Structure

### Documentation (this feature)

```text
specs/009-smart-ticker-discovery/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
packages/
├── mcp-server/
│   ├── src/
│   │   ├── agents/
│   │   │   ├── ticker.py          # MODIFY: Add sector inference logic
│   │   │   └── base.py            # No changes expected
│   │   ├── models/
│   │   │   └── agent_outputs.py   # MODIFY: Add InferredTicker, SectorOutput
│   │   └── tools/
│   │       └── ticker_search.py   # Reuse for verification
│   └── tests/
│       └── test_ticker_agent.py   # ADD: Tests for sector inference
└── extension/
    └── src/
        └── sidepanel/panel.ts     # May need minor updates for display
```

**Structure Decision**: Extend existing packages/mcp-server structure. No new packages or major restructuring required — changes are localized to TickerAgent and its output models.

## Complexity Tracking

> No violations requiring justification. Changes are localized to a single agent.
