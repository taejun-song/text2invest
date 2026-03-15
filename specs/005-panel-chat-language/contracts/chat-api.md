# API Contract: Chat with Report

## POST /api/v1/chat

Chat with an existing report using the same LLM provider configured in user settings.

### Request

```json
{
  "report_context": {
    "id": "uuid",
    "tickers": [{"symbol": "AAPL", "company_name": "Apple Inc."}],
    "thesis": "string",
    "executive_summary": ["string"],
    "risks": ["string"],
    "counter_thesis": "string",
    "confidence_score": 0.75,
    "confidence_explanation": "string",
    "catalysts": ["string"],
    "limitations": ["string"],
    "news_context": "optional summary string",
    "fundamentals_summary": "optional summary string",
    "macro_context": "optional summary string"
  },
  "messages": [
    {"role": "user", "content": "What are the main risks?"},
    {"role": "assistant", "content": "The main risks are..."},
    {"role": "user", "content": "Tell me more about the first one"}
  ],
  "user_settings": {
    "provider": "nrp",
    "model": "qwen3",
    "api_key": "...",
    "base_url": "https://ellm.nrp-nautilus.io/v1",
    "temperature": 0.7,
    "output_language": "ko"
  }
}
```

### Response (200 OK)

```json
{
  "role": "assistant",
  "content": "The response text in the selected language...",
  "timestamp": "2026-03-15T10:30:00Z"
}
```

### Response (500 Error)

```json
{
  "error": "LLM request failed",
  "message": "Timeout after 60 seconds"
}
```

### Behavior

- The server builds a system prompt from `report_context` that instructs the LLM to answer questions about the report.
- The `messages` array contains the full conversation history (max 10 messages sent by client).
- If `output_language` is set and not "en", the system prompt includes an instruction to respond in that language.
- The server uses the same `LLMProvider` class used for report generation.
- Response time target: < 15 seconds.
- No streaming — single request/response.

## Changes to Existing Endpoints

### POST /api/v1/ideas/stream (modified)

The `user_settings` object now includes an optional `output_language` field (default: `"en"`). When set, all LLM-generated text in the report is produced in the specified language.

### POST /api/v1/ideas (modified)

Same `output_language` addition to `user_settings`.
