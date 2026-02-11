# text2invest Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-11

## Active Technologies

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

- 001-text2invest-mcp-extension: Initial implementation

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
