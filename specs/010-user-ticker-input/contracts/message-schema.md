# Message Schema: User Ticker Input

## GENERATE Message

Updated message format for Chrome extension internal messaging.

### Request (Content Script → Service Worker)

```typescript
{
  type: "GENERATE",
  payload: {
    selection_text: string,    // Required, 20-8000 chars
    url: string,               // Required, source URL
    title: string,             // Required, page title
    user_tickers?: [           // Optional, user-provided tickers
      {
        symbol: string,        // Required, matches ^[A-Z0-9.\-]{1,12}$
        company_name?: string  // Optional
      }
    ]
  }
}
```

### Example

```json
{
  "type": "GENERATE",
  "payload": {
    "selection_text": "NVIDIA reported strong earnings driven by AI chip demand...",
    "url": "https://example.com/article",
    "title": "Tech Earnings Report",
    "user_tickers": [
      { "symbol": "NVDA" },
      { "symbol": "AMD" },
      { "symbol": "005930.KS", "company_name": "Samsung Electronics" }
    ]
  }
}
```

## API Request

The service worker constructs the API request for the backend:

```typescript
{
  selection_text: string,
  url: string,
  title: string,
  user_settings: UserSettings,
  user_tickers?: UserTicker[]  // Passed through from message
}
```

This matches the existing backend `IdeaRequest` model which already supports `user_tickers`.

## Validation Rules

| Field | Rule | Error Behavior |
|-------|------|----------------|
| symbol | `^[A-Z0-9.\-]{1,12}$` | UI shows invalid chip; blocked from request |
| symbol | No duplicates | Silent deduplication |
| symbol | Max 10 items | UI constraint (no generate if >10) |
