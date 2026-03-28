# UI Component Contract: Language Picker

**Feature Branch**: `013-language-picker`
**Date**: 2026-03-28

## Component: Language Select

### HTML Structure

```html
<div class="language-row">
  <select class="language-select" id="language-select">
    <option value="auto">Auto-detect</option>
    <option value="en">English</option>
    <option value="ko">Korean</option>
    <option value="ja">Japanese</option>
    <option value="zh">Chinese</option>
    <option value="es">Spanish</option>
    <option value="fr">French</option>
    <option value="de">German</option>
    <option value="pt">Portuguese</option>
    <option value="hi">Hindi</option>
    <option value="ar">Arabic</option>
  </select>
  <button class="generate-btn" id="generate-btn">Generate Report</button>
</div>
```

### CSS Specification

```css
.language-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.language-select {
  flex: 0 0 auto;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
  cursor: pointer;
  min-width: 120px;
}

.language-select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

.generate-btn {
  flex: 1;
  /* existing styles maintained */
}
```

### Event Handling

```typescript
// On language change
languageSelect.addEventListener('change', async (e) => {
  const language = (e.target as HTMLSelectElement).value;
  this.selectedLanguage = language;
  const settings = await getSettings();
  if (settings) {
    settings.output_language = language;
    await saveSettings(settings);
  }
});
```

## Integration Points

### showSelectionUI() Modifications

Location: After ticker input wrapper, before generate button

**Before**:
```html
</div> <!-- ticker-input-wrapper -->
<button class="generate-btn">Generate Report</button>
```

**After**:
```html
</div> <!-- ticker-input-wrapper -->
<div class="language-row">
  <select class="language-select" id="language-select">...</select>
  <button class="generate-btn">Generate Report</button>
</div>
```

### Initialization

```typescript
private async initLanguagePicker(): Promise<void> {
  const select = document.getElementById('language-select') as HTMLSelectElement;
  const settings = await getSettings();
  if (settings?.output_language && select) {
    select.value = settings.output_language;
    this.selectedLanguage = settings.output_language;
  }
}
```

## Accessibility

- Label via adjacent context (Generate Report button)
- Keyboard navigation via native select
- Focus states for visibility
