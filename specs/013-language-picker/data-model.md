# Data Model: Language Picker Before Generation

**Feature Branch**: `013-language-picker`
**Date**: 2026-03-28
**Phase**: 1 - Design

## Existing Types (No Changes)

### UserSettings (types/index.ts)

```typescript
export interface UserSettings {
  provider: 'openai' | 'anthropic' | 'ollama' | 'nrp';
  model: string;
  api_key?: string;
  base_url?: string;
  temperature: number;
  pii_redaction: boolean;
  web_lookup: boolean;
  agent_configs?: AgentConfig[];
  thinking_mode: boolean;
  output_language?: string;  // Used by language picker
  search_depth?: SearchDepth;
}
```

## Constants (To Add)

### Language Options (panel.ts)

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

## State Management

### PanelController (panel.ts)

New private property:
```typescript
private selectedLanguage: string = 'auto';
```

### Flow

1. **Init**: Load `output_language` from settings
2. **Selection Change**: Update dropdown display
3. **Generate**: Use current `selectedLanguage` value
4. **Storage**: Save on change via `saveSettings()`

## Storage Schema

No new keys. Uses existing:
```
chrome.storage.local:
  settings.output_language: string  // 'auto' | 'en' | 'ko' | ...
```

## Sync Behavior

| Event | Source | Action |
|-------|--------|--------|
| Panel opens | Storage | Read `output_language`, set dropdown |
| Dropdown change | Panel | Save to storage, update local state |
| Settings page save | Options | Panel reads on next generation |

## Validation Rules

- Value must be one of `LANGUAGE_OPTIONS.value`
- Default to `'auto'` if missing or invalid
- No validation errors shown to user (silent fallback)
