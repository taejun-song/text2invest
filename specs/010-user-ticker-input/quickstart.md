# Quickstart: User Ticker Input

## Prerequisites

- Node.js 18+
- Extension already built and loaded in Chrome

## Development Setup

```bash
cd packages/extension
npm install
npm run dev
```

## Implementation Order

### 1. Add Types (5 min)
Update `src/types/index.ts`:
- Add `UserTicker` interface
- Add `user_tickers` to `IdeaRequest`

### 2. Update Service Worker (10 min)
Update `src/background/service-worker.ts`:
- Add `user_tickers` to `GenerateMessage` payload type
- Pass `user_tickers` to API request

### 3. Update API Client (5 min)
Update `src/lib/api.ts`:
- Ensure `generateIdea` and `generateIdeaStream` pass `user_tickers`

### 4. Add Ticker Input UI (30 min)
Update `src/sidepanel/panel.ts`:
- Add `userTickers: TickerChip[]` state
- Add `renderTickerInput()` method
- Add chip creation on Enter/comma/Tab/blur
- Add chip removal on click
- Add validation logic
- Wire up to Generate button

### 5. Add Styles (15 min)
Update CSS (inline in panel.ts or separate file):
- `.ticker-input-container`
- `.ticker-chip` / `.ticker-chip.invalid`
- `.ticker-chip-remove`
- `.ticker-input`

### 6. Update Report Display (10 min)
Update `renderTickers()` in panel.ts:
- Add "(user)" indicator for user-provided tickers
- Add `.user-provided` CSS class

## Testing

1. Select text on any webpage
2. Open sidepanel
3. Type "AAPL" and press Enter → chip appears
4. Type "invalid123456789" and press Enter → chip appears with error style
5. Click X on a chip → chip removed
6. Click Generate → report includes user-provided tickers

## Key Files

| File | Changes |
|------|---------|
| `src/types/index.ts` | Add UserTicker, update IdeaRequest |
| `src/background/service-worker.ts` | Add user_tickers to message handling |
| `src/lib/api.ts` | Pass user_tickers in request |
| `src/sidepanel/panel.ts` | Main UI implementation |
