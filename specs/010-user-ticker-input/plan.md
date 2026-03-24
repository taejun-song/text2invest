# Implementation Plan: User Ticker Input

**Branch**: `010-user-ticker-input` | **Date**: 2026-03-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-user-ticker-input/spec.md`

## Summary

Add a ticker input UI component to the Chrome extension sidepanel that allows users to manually enter stock ticker symbols before generating investment reports. Tickers are displayed as removable chips, validated against the pattern `^[A-Z0-9.\-]{1,12}$`, and sent to the backend alongside the text selection. The backend `user_tickers` parameter support already exists from spec 009.

## Technical Context

**Language/Version**: TypeScript (Chrome Extension MV3)
**Primary Dependencies**: Chrome Extension APIs, Vite
**Storage**: chrome.storage.local (transient ticker input state not persisted)
**Testing**: Manual testing (extension), vitest (unit tests if added)
**Target Platform**: Chrome Extension MV3 (sidepanel)
**Project Type**: Multi-package (packages/extension)
**Performance Goals**: Ticker input interaction feels instant (<100ms feedback)
**Constraints**: No external dependencies for chip component; use existing CSS patterns
**Scale/Scope**: Single user, real-time interaction, 1-10 tickers typical

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution.md file found in `.specify/memory/`. Proceeding without constitution gates.

## Project Structure

### Documentation (this feature)

```text
specs/010-user-ticker-input/
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
└── extension/
    └── src/
        ├── types/
        │   └── index.ts           # MODIFY: Add UserTicker type, update IdeaRequest
        ├── lib/
        │   └── api.ts             # MODIFY: Update generateIdea to pass user_tickers
        ├── background/
        │   └── service-worker.ts  # MODIFY: Pass user_tickers from message payload
        ├── sidepanel/
        │   ├── panel.ts           # MODIFY: Add ticker input UI, chip rendering
        │   └── index.html         # MODIFY: Add ticker input markup
        └── styles/
            └── panel.css          # MODIFY: Add chip/tag styles
```

**Structure Decision**: All changes localized to packages/extension. No backend changes needed — user_tickers parameter already supported.

## Complexity Tracking

> No violations requiring justification. Changes are localized to the extension frontend.
