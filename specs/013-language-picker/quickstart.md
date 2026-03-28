# Quickstart: Language Picker Before Generation

**Feature Branch**: `013-language-picker`
**Date**: 2026-03-28

## Prerequisites

- Node.js 18+
- Extension development environment set up
- Understanding of Chrome Extension APIs

## Implementation Steps

### Step 1: Add Language Constants

File: `packages/extension/src/sidepanel/panel.ts`

Add after imports:
```typescript
const LANGUAGE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'auto', label: 'Auto-detect' },
  { value: 'en', label: 'English' },
  { value: 'ko', label: 'Korean' },
  { value: 'ja', label: 'Japanese' },
  { value: 'zh', label: 'Chinese' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'hi', label: 'Hindi' },
  { value: 'ar', label: 'Arabic' },
];
```

### Step 2: Add State Property

In `PanelController` class:
```typescript
private selectedLanguage: string = 'auto';
```

### Step 3: Modify showSelectionUI()

Replace the generate button HTML with language row:
```typescript
<div class="language-row">
  <select class="language-select" id="language-select">
    ${LANGUAGE_OPTIONS.map(opt =>
      `<option value="${opt.value}">${opt.label}</option>`
    ).join('')}
  </select>
  <button class="generate-btn" id="generate-btn">Generate Report</button>
</div>
```

### Step 4: Add CSS Styles

In the `<style>` block within `showSelectionUI()`:
```css
.language-row { display: flex; gap: 8px; align-items: center; }
.language-select { flex: 0 0 auto; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; background: #fff; cursor: pointer; min-width: 120px; }
.language-select:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,0.2); }
```

### Step 5: Bind Language Picker Events

Add new method:
```typescript
private async bindLanguagePicker(): Promise<void> {
  const select = document.getElementById('language-select') as HTMLSelectElement;
  if (!select) return;
  const settings = await getSettings();
  if (settings?.output_language) {
    select.value = settings.output_language;
    this.selectedLanguage = settings.output_language;
  }
  select.addEventListener('change', async () => {
    this.selectedLanguage = select.value;
    const settings = await getSettings();
    if (settings) {
      settings.output_language = select.value;
      await saveSettings(settings);
    }
  });
}
```

Call from `showSelectionUI()` after DOM creation.

### Step 6: Add Storage Import

Ensure `saveSettings` is imported:
```typescript
import { getReports, getEvaluations, getSettings, saveSettings, searchReports, saveEvaluation } from '../lib/storage';
```

## Testing

1. Build extension: `npm run dev`
2. Load in Chrome: `chrome://extensions/` > Load unpacked
3. Select text on any webpage
4. Open side panel
5. Verify language picker appears next to Generate button
6. Select a language and generate report
7. Verify output is in selected language
8. Check Settings page shows same language selection

## Verification Checklist

- [ ] Language picker visible when Generate button is visible
- [ ] Picker shows current language from settings
- [ ] Changing picker updates settings immediately
- [ ] Settings page reflects language picker changes
- [ ] Auto-detect works when selected
- [ ] All 10 languages are available in picker
