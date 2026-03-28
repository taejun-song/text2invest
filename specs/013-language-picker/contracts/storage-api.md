# Storage API Contract: Language Picker

**Feature Branch**: `013-language-picker`
**Date**: 2026-03-28

## Existing API (No Changes Required)

### getSettings()

```typescript
export async function getSettings(): Promise<UserSettings | null>
```

Returns current user settings including `output_language`.

### saveSettings()

```typescript
export async function saveSettings(settings: UserSettings): Promise<void>
```

Persists settings to `chrome.storage.local`.

## Usage Pattern

### Read Language Preference

```typescript
const settings = await getSettings();
const language = settings?.output_language || 'auto';
```

### Update Language Preference

```typescript
const settings = await getSettings();
if (settings) {
  settings.output_language = 'ko';  // or any valid language code
  await saveSettings(settings);
}
```

## Valid Language Values

| Code | Language |
|------|----------|
| `auto` | Auto-detect from input text |
| `en` | English |
| `ko` | Korean |
| `ja` | Japanese |
| `zh` | Chinese |
| `es` | Spanish |
| `fr` | French |
| `de` | German |
| `pt` | Portuguese |
| `hi` | Hindi |
| `ar` | Arabic |

## Sync Guarantees

- Changes via panel picker visible in Options page on refresh
- Changes via Options page visible in panel on next `showSelectionUI()` call
- No real-time sync listener required (read on demand)
