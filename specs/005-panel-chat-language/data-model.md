# Data Model: Panel Chat & Language Selection

**Feature**: 005-panel-chat-language
**Date**: 2026-03-15

## Entities

### ChatMessage

A single message in a chat conversation about a report.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| role | `"user" \| "assistant"` | Yes | Who sent the message |
| content | string | Yes | Message text |
| timestamp | string (ISO 8601) | Yes | When the message was sent |

**Lifecycle**: Created when user sends a message or when assistant responds. Exists only in memory (side panel state). Cleared when user switches reports or closes the panel.

### ChatSession

In-memory collection of messages for the current report. Not a persisted entity.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| report_id | string (UUID) | Yes | ID of the associated report |
| messages | ChatMessage[] | Yes | Ordered list of messages |

**Lifecycle**: Created when user opens chat tab for a report. Cleared when a different report is loaded.

### UserSettings (modified)

Add one new field to the existing `UserSettings` model.

| New Field | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| output_language | string | No | `"en"` | Locale code for LLM output language |

**Persistence**: `chrome.storage.local` (extension), passed to server via `IdeaRequest.user_settings`.

## Supported Languages

| Code | Display Name |
|------|-------------|
| en | English |
| ko | Korean |
| ja | Japanese |
| zh | Chinese (Simplified) |
| es | Spanish |
| fr | French |
| de | German |
| pt | Portuguese |
| hi | Hindi |
| ar | Arabic |

## State Transitions

### Chat Flow

```
No Report → [report generated] → Report View
Report View → [click Chat tab] → Chat View (empty session)
Chat View → [send message] → Chat View (loading)
Chat View (loading) → [response received] → Chat View (messages)
Chat View (messages) → [send another] → Chat View (loading)
Chat View → [switch report] → Chat View (empty session, new report_id)
Chat View → [click Report tab] → Report View
```

### Language Selection Flow

```
Settings → [select language] → [save] → Settings (persisted)
Generate Report → [reads output_language from settings] → Report in selected language
Chat → [reads output_language from settings] → Chat response in selected language
```
