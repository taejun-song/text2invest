# text2invest Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-11

## Active Technologies
- Python 3.13 (MCP server), TypeScript (Chrome Extension) + FastMCP 2.x, LiteLLM, Pydantic 2.x, duckduckgo-search (server); Chrome Extension APIs (client) (002-multi-agent-data)
- Python 3.13 (server), TypeScript (extension) + LiteLLM, FastAPI, Pydantic 2.x (server); Chrome Extension APIs MV3 (client) (004-thinking-mode-panel)
- chrome.storage.local (extension settings + report history) (004-thinking-mode-panel)
- Python 3.13 (MCP server), TypeScript (Chrome Extension MV3) + FastAPI, LiteLLM, Pydantic 2.x (server); Chrome Extension APIs, Vite (client) (005-panel-chat-language)
- `chrome.storage.local` (extension settings, reports), in-memory (server) (005-panel-chat-language)

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
- 005-panel-chat-language: Added Python 3.13 (MCP server), TypeScript (Chrome Extension MV3) + FastAPI, LiteLLM, Pydantic 2.x (server); Chrome Extension APIs, Vite (client)
- 004-thinking-mode-panel: Added Python 3.13 (server), TypeScript (extension) + LiteLLM, FastAPI, Pydantic 2.x (server); Chrome Extension APIs MV3 (client)
- 002-multi-agent-data: Added Python 3.13 (MCP server), TypeScript (Chrome Extension) + FastMCP 2.x, LiteLLM, Pydantic 2.x, duckduckgo-search (server); Chrome Extension APIs (client)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
