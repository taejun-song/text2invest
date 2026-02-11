# Quickstart: Text2Invest Development

## Prerequisites

- Python 3.13+
- Node.js 20+
- uv (Python package manager)
- Chrome or Edge browser

## Repository Setup

```bash
# Clone and enter repo
cd text2invest

# Install Python dependencies
cd packages/mcp-server
uv sync

# Install extension dependencies
cd ../extension
npm install
```

## Running the MCP Server

```bash
cd packages/mcp-server

# Development mode with auto-reload
uv run fastmcp dev src/server.py

# Server runs at http://localhost:8000
```

## Building the Extension

```bash
cd packages/extension

# Development build with watch
npm run dev

# Production build
npm run build

# Output in dist/
```

## Loading the Extension in Chrome

1. Open `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select `packages/extension/dist/`

## First Test

1. Start the MCP server
2. Load the extension
3. Open extension settings, configure LLM provider:
   - **OpenAI**: Enter API key
   - **Anthropic**: Enter API key
   - **Ollama**: Enter base URL (e.g., `http://localhost:11434`)
4. Navigate to any webpage with investment-relevant text
5. Select text (minimum 20 characters)
6. Click "Generate idea" in the popup
7. View report in side panel

## Project Scripts

### MCP Server (packages/mcp-server)

| Command | Description |
|---------|-------------|
| `uv run fastmcp dev src/server.py` | Start dev server |
| `uv run pytest` | Run tests |
| `uv run pytest --cov` | Run tests with coverage |

### Extension (packages/extension)

| Command | Description |
|---------|-------------|
| `npm run dev` | Development build with watch |
| `npm run build` | Production build |
| `npm run lint` | Lint TypeScript |
| `npm run test` | Run E2E tests |

## Environment Variables

### MCP Server

Create `.env` in `packages/mcp-server/`:

```bash
# Optional: Default port (default: 8000)
MCP_PORT=8000

# Optional: Log level (default: INFO)
LOG_LEVEL=DEBUG
```

### Extension

No environment variables required. All configuration is user-provided through the settings UI.

## Testing with Different Providers

### OpenAI

1. Get API key from https://platform.openai.com/api-keys
2. Enter in extension settings
3. Recommended model: `gpt-4-turbo`

### Anthropic

1. Get API key from https://console.anthropic.com/
2. Enter in extension settings
3. Recommended model: `claude-3-5-sonnet-20241022`

### Ollama (Local)

1. Install Ollama: https://ollama.com/
2. Pull a model: `ollama pull llama3.1`
3. Start Ollama: `ollama serve`
4. In extension settings:
   - Provider: Ollama
   - Base URL: `http://localhost:11434`
   - Model: `llama3.1`

## Debugging

### MCP Server Logs

```bash
# View server logs
uv run fastmcp dev src/server.py --log-level DEBUG
```

### Extension Debugging

1. Open `chrome://extensions/`
2. Click "Inspect views: service worker" on the extension
3. Check Console for background script logs
4. Right-click the popup/side panel → Inspect for UI logs

### Network Requests

1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Filter by `localhost:8000` to see MCP API calls

## Common Issues

| Issue | Solution |
|-------|----------|
| "Provider not configured" | Open extension settings and add API key |
| "Text too short" | Select at least 20 characters |
| "Connection refused" | Ensure MCP server is running |
| "Rate limited" | Wait and retry, or switch models |
| "Schema validation failed" | Check server logs for details |
