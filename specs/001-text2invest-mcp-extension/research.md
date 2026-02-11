# Research: Text2Invest Technical Decisions

**Date**: 2026-02-11
**Feature**: Text2Invest MCP Extension

## MCP Server Framework

**Decision**: FastMCP 2.x with Python 3.13

**Rationale**:
- Official MCP SDK abstraction that handles protocol complexity
- Automatic schema generation from Pydantic type hints
- Built-in HTTP transport for browser extension communication
- Native async/await support optimized in Python 3.13

**Alternatives Considered**:
- Raw `mcp` SDK: More verbose, manual schema definitions required
- Custom HTTP server: Would need to implement MCP protocol from scratch

## LLM Provider Abstraction

**Decision**: LiteLLM

**Rationale**:
- Unified interface for 100+ providers (OpenAI, Anthropic, Ollama)
- Single API for all models - simplifies multi-provider support
- Built-in cost tracking and model fallback
- Works with local Ollama without code changes

**Alternatives Considered**:
- Direct provider SDKs: Requires separate code paths per provider
- LLMSwap: Less mature, fewer features

## Schema Validation

**Decision**: Pydantic 2.x

**Rationale**:
- Native FastMCP integration - schemas auto-generated from models
- Strict validation with clear error messages
- JSON Schema export for cross-language sharing (TypeScript types)
- Python 3.13 performance improvements benefit Pydantic

**Alternatives Considered**:
- marshmallow: Less integrated with FastMCP
- attrs + cattrs: Requires more manual validation code

## Browser Extension Framework

**Decision**: Chrome Extension MV3 with TypeScript

**Rationale**:
- MV3 required for Chrome Web Store (MV2 deprecated)
- TypeScript catches type errors at compile time
- Strong tooling ecosystem (webpack, Rollup)
- Types can be generated from Pydantic schemas for consistency

**Alternatives Considered**:
- Plain JavaScript: No compile-time safety
- Plasmo/WXT frameworks: Adds complexity, learning curve

## Extension-Server Communication

**Decision**: HTTP (localhost) with JSON

**Rationale**:
- Simple request/response pattern fits the use case
- No persistent connection needed (generation is request-based)
- Works with service worker lifecycle (ephemeral)
- FastMCP provides HTTP transport out of the box

**Alternatives Considered**:
- WebSocket: Overkill for request-response pattern
- Native messaging: Requires native host installation

## Local Storage

**Decision**: chrome.storage.local

**Rationale**:
- MV3 service workers cannot use localStorage
- Async API aligns with service worker patterns
- Cross-context access (popup, side panel, content script)
- Adequate quota for hundreds of reports

**Alternatives Considered**:
- IndexedDB: More complex API, overkill for structured reports
- File system API: Limited browser support, complex permissions

## Testing Strategy

**Decision**: pytest (server) + Playwright (extension E2E)

**Rationale**:
- pytest is standard for Python, integrates with FastMCP
- Playwright supports Chrome extension testing
- Enables full E2E flows (select text → generate → view report)

**Alternatives Considered**:
- Jest + Puppeteer: Less mature extension support
- Manual testing: Not scalable, no regression protection

## Project Structure

**Decision**: Monorepo with packages/ directory

**Rationale**:
- Shared schemas between Python and TypeScript
- Single repo simplifies version coordination
- uv (Python) and npm (TypeScript) coexist cleanly
- CI/CD can build all components together

**Alternatives Considered**:
- Separate repos: Harder to keep schemas in sync
- Single flat structure: Confusing dependency boundaries

## Agent Pipeline Architecture

**Decision**: Sequential 7-stage pipeline with per-stage validation

**Rationale**:
- Each agent has single responsibility (testable, debuggable)
- Schema validation between stages catches errors early
- Different stages can use different models (cost optimization)
- Retry logic isolated per stage (max 3 retries each)

**Stages**:
1. **Extraction Agent**: Clean and normalize selected text
2. **Entity Agent**: Identify companies, products, macro terms
3. **Ticker Agent**: Map companies to tickers with uncertainty
4. **Thesis Agent**: Generate investment thesis grounded in text
5. **Critique Agent**: Identify risks, counter-arguments, missing info
6. **Confidence Agent**: Calibrate overall confidence score
7. **Formatter Agent**: Enforce final IdeaReport schema

**Alternatives Considered**:
- Single mega-prompt: No transparency, hard to debug
- Parallel agents: Dependencies prevent parallelism here
- Graph-based orchestration: Overkill for linear pipeline

## PII Redaction

**Decision**: Regex-based detection before sending to LLM

**Rationale**:
- Simple, predictable, no external dependencies
- Patterns for email and phone numbers are well-established
- Runs client-side (extension) before any network transmission
- User can disable if needed

**Alternatives Considered**:
- LLM-based detection: Slower, sends PII to detect PII
- Third-party APIs: Privacy contradiction

## Key Package Versions

| Package | Version | Purpose |
|---------|---------|---------|
| fastmcp | 2.2.6+ | MCP server framework |
| mcp | 1.7.1+ | Core MCP SDK |
| litellm | latest | LLM provider abstraction |
| pydantic | 2.x | Schema validation |
| pytest | 8.x | Python testing |
| typescript | 5.x | Extension development |
