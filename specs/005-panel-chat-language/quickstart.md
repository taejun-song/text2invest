# Quickstart: Panel Chat & Language Selection

## Prerequisites

1. MCP server running: `cd packages/mcp-server && uv run python src/api_server.py`
2. Extension built: `cd packages/extension && npm run build`
3. Extension loaded in Chrome (developer mode)

## Test Scenarios

### Scenario 1: Progress Display (US1)

1. Navigate to any news article about a public company
2. Select text containing company/financial information
3. Click "Generate Idea" from the floating tooltip
4. Observe the side panel:
   - Stage checklist appears with extraction → entity → ticker → thesis → critique → confidence → enrichment → formatting
   - Active stage shows spinner, completed stages show checkmark
   - Elapsed timer counts up in mm:ss format
   - Data agent results appear inline (e.g., "3 news articles", "P/E: 36.8")
   - When complete, view transitions to full report

### Scenario 2: Chat with Report (US2)

1. After a report is generated (from Scenario 1)
2. Click the "Chat" tab in the side panel header
3. Type: "What are the main risks?"
4. Click Send (or press Enter)
5. Observe:
   - Typing indicator appears
   - Send button disables during generation
   - Response appears referencing specific risks from the report
6. Ask a follow-up: "Explain the first risk in more detail"
7. Verify response maintains context from previous exchange
8. Switch to History tab, click a different report
9. Verify chat clears with a notice

### Scenario 3: Output Language (US3)

1. Open extension settings (right-click extension icon → Options)
2. Find "Output Language" dropdown
3. Select "Korean" (한국어)
4. Save settings
5. Generate a new report
6. Verify:
   - Thesis is in Korean
   - Executive summary bullets are in Korean
   - Risks, counter-thesis, confidence explanation are in Korean
   - Ticker symbols (AAPL) remain in English
   - Numerical values remain unchanged
7. Open Chat tab, ask a question in Korean or English
8. Verify response comes back in Korean
9. Close and reopen browser, verify language is still set to Korean

### Scenario 4: RTL Language (Edge Case)

1. Set output language to Arabic
2. Generate a report
3. Verify text displays right-to-left
4. Open chat, verify RTL text direction

### Scenario 5: Chat Error Handling (Edge Case)

1. Stop the MCP server
2. Open chat on an existing report
3. Send a message
4. Verify error message appears with "Retry" button
5. Restart server, click Retry, verify response appears
