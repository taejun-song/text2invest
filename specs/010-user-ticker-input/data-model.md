# Data Model: User Ticker Input

## TypeScript Types (Extension)

### UserTicker

Represents a user-provided ticker symbol.

```typescript
interface UserTicker {
  symbol: string;        // e.g., "AAPL", "005930.KS"
  company_name?: string; // Optional, populated by autocomplete (P3)
}
```

**Validation**: `symbol` must match pattern `^[A-Z0-9.\-]{1,12}$`

### IdeaRequest (Updated)

Add optional `user_tickers` field to existing interface.

```typescript
interface IdeaRequest {
  selection_text: string;
  url: string;
  title: string;
  user_settings: UserSettings;
  user_tickers?: UserTicker[];  // NEW: User-provided tickers
}
```

### GenerateMessage (Updated)

Add `user_tickers` to message payload passed to service worker.

```typescript
interface GenerateMessage extends Message {
  type: 'GENERATE';
  payload: {
    selection_text: string;
    url: string;
    title: string;
    user_tickers?: UserTicker[];  // NEW
  };
}
```

## UI State (Panel Controller)

### TickerChip (Internal)

Represents a chip in the ticker input component.

```typescript
interface TickerChip {
  symbol: string;    // Normalized (uppercase, trimmed)
  isValid: boolean;  // Passes regex validation
}
```

**State location**: `PanelController.userTickers: TickerChip[]`

## Data Flow

```
User types "aapl" → Press Enter
    ↓
Normalize to "AAPL"
    ↓
Validate against ^[A-Z0-9.\-]{1,12}$
    ↓
Add TickerChip { symbol: "AAPL", isValid: true }
    ↓
Render chip in UI

User clicks Generate
    ↓
Filter chips where isValid === true
    ↓
Map to UserTicker[] (drop isValid flag)
    ↓
Include in GENERATE message payload
    ↓
Service worker passes to IdeaRequest
    ↓
Backend merges with LLM-detected tickers
```

## Relationship to Backend

The backend `UserTicker` model (from spec 009) matches the extension type:

```python
# packages/mcp-server/src/models/idea_report.py
class UserTicker(BaseModel):
    symbol: str = Field(..., pattern=r"^[A-Z0-9.\-]{1,12}$")
    company_name: str | None = None
```

No backend changes needed — the extension types align with existing API contract.
