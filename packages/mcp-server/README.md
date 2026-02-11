# Text2Invest MCP Server

MCP server for Text2Invest - generates structured investment ideas from text using a 7-stage AI agent pipeline.

## Setup

```bash
uv sync
uv run fastmcp dev src/server.py
```

## Features

- Extraction, Entity, Ticker, Thesis, Critique, Confidence, Formatter agents
- Multi-provider LLM support via LiteLLM (OpenAI, Anthropic, Ollama)
- Structured output with Pydantic validation
