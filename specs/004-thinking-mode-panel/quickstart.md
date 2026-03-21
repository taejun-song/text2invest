# Quickstart: Thinking Mode Toggle & Display

## Prerequisites

- API server running: `cd packages/mcp-server && uv run python src/api_server.py`
- Extension built: `cd packages/extension && npm run build`
- Extension loaded in Chrome (developer mode)

## Test Scenarios

### Scenario 1: Enable Thinking Mode and See Thinking Output

1. Open extension options (right-click extension icon → Options)
2. Toggle "Thinking Mode" ON
3. Navigate to a financial news article
4. Select 20+ characters of text
5. Click "Generate Idea" on the floating tooltip
6. Observe the side panel:
   - Thinking section appears with agent labels
   - Thinking tokens stream in real-time under each agent's section
   - Auto-scroll follows new content
7. When generation completes:
   - Thinking sections collapse
   - Report displays below

**Expected**: Thinking text visible in real-time, grouped by pipeline phase.

### Scenario 2: Disable Thinking Mode

1. Open extension options
2. Toggle "Thinking Mode" OFF
3. Generate a report
4. Observe the side panel:
   - No thinking section appears
   - Only stage progress shown (same as current behavior)
   - Generation completes faster

**Expected**: No thinking UI, faster generation.

### Scenario 3: Open Panel from Popup

1. Click the extension icon to open popup
2. Click "Open Panel" button
3. Side panel opens showing last report or idle state

**Expected**: Panel opens regardless of generation state.

### Scenario 4: Thinking in Export

1. Generate a report with thinking mode ON
2. Click "Export Markdown"
3. Check the exported file:
   - Report content appears first
   - Thinking output appears in a `<details>` block at the end

**Expected**: Thinking included as collapsible section in export.

### Scenario 5: Non-Thinking Model Fallback

1. Switch provider to OpenAI or Ollama (non-Qwen model)
2. Enable thinking mode
3. Generate a report
4. Observe: no thinking section appears, no errors

**Expected**: Graceful fallback, no thinking UI shown.
