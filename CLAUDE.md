# text2invest Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-11

## Active Technologies
- Python 3.13 (MCP server), TypeScript (Chrome Extension) + FastMCP 2.x, LiteLLM, Pydantic 2.x, duckduckgo-search (server); Chrome Extension APIs (client) (002-multi-agent-data)
- Python 3.13 (server), TypeScript (extension) + LiteLLM, FastAPI, Pydantic 2.x (server); Chrome Extension APIs MV3 (client) (004-thinking-mode-panel)
- chrome.storage.local (extension settings + report history) (004-thinking-mode-panel)
- Python 3.13 (MCP server), TypeScript (Chrome Extension MV3) + FastAPI, LiteLLM, Pydantic 2.x (server); Chrome Extension APIs, Vite (client) (005-panel-chat-language)
- `chrome.storage.local` (extension settings, reports), in-memory (server) (005-panel-chat-language)
- Python 3.13 (MCP server), TypeScript (Chrome Extension MV3) + FastMCP 2.x, LiteLLM, Pydantic 2.x, Chrome Extension APIs (006-ticker-recommendation)
- Python 3.13 (MCP server), TypeScript (Chrome Extension MV3) + FastMCP 2.x, LiteLLM, Pydantic 2.x (server); Chrome Extension APIs, Vite (client) (008-locale-output-defaults)
- chrome.storage.local (extension settings) (008-locale-output-defaults)
- Python 3.13 + FastMCP 2.x, LiteLLM, Pydantic 2.x, yfinance, rapidfuzz (009-smart-ticker-discovery)
- N/A (in-memory processing only) (009-smart-ticker-discovery)

- **Python 3.13**: MCP server (FastMCP 2.x, LiteLLM, Pydantic 2.x)
- **TypeScript**: Chrome Extension (MV3)
- **Storage**: chrome.storage.local (extension), in-memory (server)

## Project Structure

```text
packages/
├── core/           # Shared schemas (JSON Schema)
├── mcp-server/     # Python FastMCP server
└── extension/      # Chrome Extension (MV3)
```

## Commands

### MCP Server

```bash
cd packages/mcp-server
uv sync                          # Install dependencies
uv run fastmcp dev src/server.py # Start dev server
uv run pytest                    # Run tests
```

### Extension

```bash
cd packages/extension
npm install    # Install dependencies
npm run dev    # Development build
npm run build  # Production build
```

## Code Style

- **Python**: ruff for linting, black for formatting
- **TypeScript**: ESLint + Prettier

## Recent Changes
- 009-smart-ticker-discovery: Added Python 3.13 + FastMCP 2.x, LiteLLM, Pydantic 2.x, yfinance, rapidfuzz
- 008-locale-output-defaults: Added Python 3.13 (MCP server), TypeScript (Chrome Extension MV3) + FastMCP 2.x, LiteLLM, Pydantic 2.x (server); Chrome Extension APIs, Vite (client)
- 006-ticker-recommendation: Added Python 3.13 (MCP server), TypeScript (Chrome Extension MV3) + FastMCP 2.x, LiteLLM, Pydantic 2.x, Chrome Extension APIs


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
