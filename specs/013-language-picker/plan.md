# Implementation Plan: Language Picker Before Generation

**Branch**: `013-language-picker` | **Date**: 2026-03-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/013-language-picker/spec.md`

## Summary

Add a language selection dropdown next to the Generate Report button in the side panel, allowing users to choose the output language before generating investment reports. The picker syncs with existing Settings page language preference and persists across sessions.

## Technical Context

**Language/Version**: TypeScript 5.x (Chrome Extension)
**Primary Dependencies**: Chrome Extension APIs MV3, Vite
**Storage**: chrome.storage.local (extension settings)
**Testing**: Manual testing via extension reload
**Target Platform**: Chrome Extension (Chromium browsers)
**Project Type**: Browser extension with side panel UI
**Performance Goals**: Instant UI response (<100ms)
**Constraints**: Side panel space constraints, sync with Settings page
**Scale/Scope**: Single dropdown, 11 language options

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] No new npm dependencies required
- [x] Reuses existing storage API
- [x] Follows existing UI patterns
- [x] No backend changes required

## Project Structure

### Documentation (this feature)

```text
specs/013-language-picker/
├── plan.md              # This file
├── research.md          # Phase 0 output - codebase analysis
├── data-model.md        # Phase 1 output - type definitions
├── quickstart.md        # Phase 1 output - implementation steps
├── contracts/           # Phase 1 output - component specs
│   ├── ui-components.md
│   └── storage-api.md
└── tasks.md             # Phase 2 output (TBD)
```

### Source Code (repository root)

```text
packages/extension/
├── src/
│   ├── sidepanel/
│   │   ├── panel.ts     # Main modification: add language picker
│   │   └── index.html   # CSS styles for language picker
│   ├── lib/
│   │   └── storage.ts   # No changes - use existing API
│   └── types/
│       └── index.ts     # No changes - use existing UserSettings
└── ...
```

**Structure Decision**: Monorepo with packages/extension containing all Chrome Extension code. Language picker implementation isolated to sidepanel module.

## Key Implementation Details

### Files to Modify

| File | Change | Lines |
|------|--------|-------|
| `packages/extension/src/sidepanel/panel.ts` | Add language picker UI, event handlers | ~50 |
| `packages/extension/src/sidepanel/index.html` | Add CSS for language-row, language-select | ~15 |

### UI Layout

```
┌─────────────────────────────────────┐
│ Selection Preview                    │
├─────────────────────────────────────┤
│ Add tickers (optional)               │
│ ┌─────────────────────────────────┐ │
│ │ AAPL × │ MSFT × │              │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ ┌──────────────┐ ┌────────────────┐ │
│ │ Auto-detect ▼│ │Generate Report │ │
│ └──────────────┘ └────────────────┘ │
└─────────────────────────────────────┘
```

### Language Options

| Code | Display |
|------|---------|
| auto | Auto-detect |
| en | English |
| ko | Korean |
| ja | Japanese |
| zh | Chinese |
| es | Spanish |
| fr | French |
| de | German |
| pt | Portuguese |
| hi | Hindi |
| ar | Arabic |

## Complexity Tracking

> No constitution violations. Feature is minimal and uses existing infrastructure.

| Aspect | Status | Notes |
|--------|--------|-------|
| Dependencies | None added | Uses existing chrome.storage |
| Storage | Reused | Existing output_language field |
| Backend | No changes | Already supports language param |
| Testing | Manual | Extension reload workflow |
