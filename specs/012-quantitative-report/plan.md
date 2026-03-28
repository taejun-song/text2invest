# Implementation Plan: Quantitative Investment Report

**Branch**: `012-quantitative-report` | **Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/012-quantitative-report/spec.md`

## Summary

Replace subjective confidence scores with objective quantitative metrics in investment reports. Add technical indicators (moving averages, RSI) alongside existing fundamental data. Remove confidence_score field entirely and present data-driven metrics users can interpret themselves.

## Technical Context

**Language/Version**: Python 3.13 (MCP server), TypeScript (Chrome Extension)
**Primary Dependencies**: FastMCP 2.x, LiteLLM, Pydantic 2.x, yfinance (server); Chrome Extension APIs (client)
**Storage**: SQLite (fundamentals cache from spec 011), chrome.storage.local (extension)
**Testing**: Manual testing per quickstart.md
**Target Platform**: Linux/macOS server, Chrome browser
**Project Type**: Web application (backend + browser extension)
**Performance Goals**: Report generation under 10 seconds
**Constraints**: Use existing yfinance provider for technical data
**Scale/Scope**: Same as existing system

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file present - proceeding with standard practices:
- ✅ Follows existing project patterns (providers, models, agents)
- ✅ Uses established data sources (yfinance)
- ✅ No new external dependencies required for technical indicators

## Project Structure

### Documentation (this feature)

```text
specs/012-quantitative-report/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
packages/
├── mcp-server/
│   └── src/
│       ├── models/
│       │   ├── fundamentals.py      # Extend with TechnicalIndicators
│       │   └── idea_report.py       # Remove confidence_score
│       ├── providers/
│       │   └── fundamentals/
│       │       ├── yfinance_provider.py  # Add technical data methods
│       │       └── service.py            # Add get_technical_indicators()
│       └── agents/
│           └── collaborative/
│               └── fundamentals.py  # Include technical data in output
└── extension/
    └── src/
        └── sidepanel/
            └── panel.ts             # Update report display
```

**Structure Decision**: Extends existing MCP server structure, modifies fundamentals provider to include technical indicators, updates report model to remove confidence_score.

## Complexity Tracking

No violations - feature fits within existing architecture.
