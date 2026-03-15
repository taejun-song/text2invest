# Text2Invest

A Chrome extension + MCP server that turns selected text into investment analysis reports using multi-agent collaboration.

## Project Structure

```
packages/
  core/         # Shared JSON schemas
  mcp-server/   # Python FastMCP server (LiteLLM, Pydantic)
  extension/    # Chrome Extension (MV3, TypeScript, Vite)
```

## Setup

### 1. API Server

```bash
cd packages/mcp-server
uv sync
uv run python src/api_server.py
```

### 2. Chrome Extension

```bash
cd packages/extension
npm install
```

Create a `.env` file in `packages/extension/`:

```env
VITE_DEFAULT_PROVIDER=nrp
VITE_DEFAULT_API_KEY=your-api-key-here
VITE_DEFAULT_BASE_URL=https://ellm.nrp-nautilus.io/v1
VITE_DEFAULT_MODEL=qwen3
```

Then build:

```bash
npm run build
```

Load in Chrome:

1. Go to `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked** and select `packages/extension/dist/`

## Usage

1. Navigate to any webpage with financial content
2. Select text (20+ characters)
3. A floating "Generate Idea" tooltip appears near the selection — click it
4. View the enriched report in the side panel

## Data Agents

| Agent | Description |
|-------|-------------|
| News Agent | Searches recent news about identified companies |
| Fundamentals Agent | Retrieves financial metrics for public companies |
| Risk Agent | Cross-references findings to identify risks |
| Macro Agent | Adds macro-economic context (sector trends, indicators) |

Agents can be individually enabled/disabled in the extension settings.
