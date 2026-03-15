# Quickstart: Multi-Agent Collaborative Investment Analysis

## Prerequisites

- Python 3.13+
- Node.js 20+
- uv (Python package manager)
- Chrome or Edge browser
- NRP.ai API token (provided)

## Setup

```bash
cd packages/mcp-server
uv sync
cd ../extension
npm install
```

## Configuration

### NRP.ai Provider

In extension settings, configure:
- **Provider**: NRP.ai
- **Model**: `qwen3`
- **API Key**: Your NRP.ai token
- **Base URL**: `https://ellm.nrp-nautilus.io/v1`

### Agent Configuration

In extension settings under "Data Agents":
- **News Agent**: Enabled by default. Searches for recent news about identified companies.
- **Fundamentals Agent**: Enabled by default. Retrieves financial metrics for public companies.
- **Risk Agent**: Always active. Cross-references findings from other agents.
- **Macro Agent**: Disabled by default. Adds macro-economic context.

Each agent can individually toggle external data lookups (web search) on/off.

## Running

```bash
# Start MCP server
cd packages/mcp-server
uv run fastmcp dev src/server.py

# Build extension (separate terminal)
cd packages/extension
npm run dev
```

Load the extension in Chrome:
1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" → select `packages/extension/dist/`

## First Enriched Analysis

1. Start the MCP server
2. Load the extension
3. Configure NRP.ai provider in settings
4. Enable desired data agents
5. Navigate to a news article about a public company
6. Select text (minimum 20 characters)
7. Click "Generate idea"
8. View enriched report in side panel — look for News Context, Fundamentals, and Cross-Reference sections
9. Click "Agent Log" to see inter-agent communication

## Testing Scenarios

### Basic Enrichment
Select text mentioning "Apple earnings" → Verify report includes news context and fundamental metrics.

### Graceful Degradation
Disable all data agents in settings → Generate idea → Verify text-only report with no enrichment sections.

### Cross-Reference Divergence
Select text with positive news about a company → If fundamentals show concerns, verify the Cross-Reference section flags the divergence.

### Agent Transparency
Generate any enriched report → Check that each section shows which agent produced it.

## Project Scripts

### MCP Server

| Command | Description |
|---------|-------------|
| `uv run fastmcp dev src/server.py` | Start dev server |
| `uv run pytest` | Run tests |
| `uv run pytest --cov` | Run tests with coverage |

### Extension

| Command | Description |
|---------|-------------|
| `npm run dev` | Development build with watch |
| `npm run build` | Production build |
| `npm run lint` | Lint TypeScript |

## Common Issues

| Issue | Solution |
|-------|----------|
| "NRP.ai unavailable" | Check network, verify API token, retry |
| "No enrichment data" | Ensure data agents are enabled and web lookup is ON in settings |
| "Agent timeout" | Enriched analysis may take up to 60s; wait or reduce enabled agents |
| "No news found" | Web search may not find results for obscure topics; report shows text-only analysis |
