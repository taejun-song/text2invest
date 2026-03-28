# Research: Language Picker Before Generation

**Feature Branch**: `013-language-picker`
**Date**: 2026-03-28
**Phase**: 0 - Research

## Existing Codebase Analysis

### Current Language Infrastructure

**Settings Storage** (`packages/extension/src/lib/storage.ts:19`):
- `output_language` stored in `UserSettings` with default value `'auto'`
- Persisted via `chrome.storage.local`
- Auto-migration from `'en'` to `'auto'` for backward compatibility

**Options Page** (`packages/extension/src/options/options.ts:94`):
- `outputLanguageSelect` handles language selection in Settings
- Saves via `saveSettings()` function
- Available languages: auto, en, ko, ja, zh, es, fr, de, pt, hi, ar

**Type Definition** (`packages/extension/src/types/index.ts:134`):
```typescript
output_language?: string;
```

### Side Panel Generation Flow

**Generate Button Location** (`packages/extension/src/sidepanel/panel.ts:70-108`):
- `showSelectionUI()` creates the selection UI container
- Contains: selection preview, ticker input, and Generate button
- Inserted at `contentEl.insertBefore(container, contentEl.firstChild)`

**Current UI Structure**:
```html
<div id="selection-ui">
  <div class="selection-preview">...</div>
  <div class="ticker-label">Add tickers (optional)</div>
  <div class="ticker-input-wrapper">...</div>
  <button class="generate-btn">Generate Report</button>
</div>
```

**Generation Trigger** (`packages/extension/src/sidepanel/panel.ts:280-297`):
- `triggerGenerate()` sends `GENERATE` message with selection data
- Settings are loaded from storage via `getSettings()`
- `output_language` is passed as part of `user_settings` in the request

### Backend Integration

**Service Worker** (`packages/extension/src/background/service-worker.ts:100-228`):
- `handleGenerate()` loads settings via `getSettings()`
- Creates `IdeaRequest` with `user_settings: settings`
- Sends to API via `generateIdeaStream()`

**Settings Flow**:
1. User selects language in Settings page
2. Saved to `chrome.storage.local`
3. On Generate, settings loaded and sent to backend
4. Backend uses `output_language` for report generation

## Integration Points

### Where to Add Language Picker

The language picker should be added to `showSelectionUI()` in `panel.ts`:
- Location: Between ticker input and Generate button (line 106-107)
- Style: Inline with Generate button for compact layout

### Storage Synchronization

The language picker must:
1. Read current `output_language` from settings on panel open
2. Update settings when language changes
3. Sync with Options page (bidirectional)

### Supported Languages

From Options page analysis:
- `auto` - Auto-detect from input text
- `en` - English
- `ko` - Korean
- `ja` - Japanese
- `zh` - Chinese
- `es` - Spanish
- `fr` - French
- `de` - German
- `pt` - Portuguese
- `hi` - Hindi
- `ar` - Arabic

## Technical Decisions

### UI Approach

**Recommended**: Compact select dropdown next to Generate button
- Minimal vertical space usage
- Familiar HTML select pattern
- Consistent with existing dropdown styles

**Alternative Considered**: Radio buttons or chip selector
- Rejected: Takes too much space for 10+ options

### State Management

- Use existing `getSettings()` / `saveSettings()` from `storage.ts`
- No new storage keys needed - reuse `output_language`
- Panel controller reads settings on init and selection change

### Auto-Detect Implementation

- Already supported by backend (see `api_server.py:14` auto-detection)
- Panel passes `output_language: 'auto'` to let backend detect
- No additional frontend logic needed for auto-detect

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `packages/extension/src/sidepanel/panel.ts` | Edit | Add language picker UI in `showSelectionUI()` |
| `packages/extension/src/sidepanel/index.html` | Edit | Add styles for language picker |
| `packages/extension/src/lib/storage.ts` | None | No changes needed - use existing API |
| `packages/extension/src/options/options.ts` | None | Sync handled automatically via storage |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Options page desync | Low | Medium | Both read from same storage key |
| RTL language styling | Low | Low | Out of scope per spec |
| Mobile/narrow viewport | Low | Low | Use responsive flex layout |

## Dependencies

- No new npm packages required
- No backend changes required
- Existing language detection in backend supports all listed languages
