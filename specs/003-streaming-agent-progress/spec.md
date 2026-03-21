# Feature Specification: Real-Time Streaming Agent Progress

**Feature Branch**: `003-streaming-agent-progress`
**Created**: 2026-03-15
**Status**: Draft
**Input**: User description: "okay it changed, but still Extracting text... forever which is really bad experience even if it works in the end, so you should expand the thought process showing the streaming of each agent"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Live Stage-by-Stage Progress (Priority: P1)

As a user generating an investment report, I want to see a live checklist of pipeline stages updating in real-time so I know exactly what the system is doing and don't think it's frozen.

Currently the side panel shows "Extracting text..." for the entire generation (which can take 30-60+ seconds), creating the impression the system is stuck. Instead, the user should see each stage transition as it happens (extraction → entity identification → ticker mapping → thesis → critique → confidence → enrichment → formatting) with clear visual indicators (spinner for active, checkmark for done, grey circle for pending).

**Why this priority**: The current "stuck at Extracting text..." experience is the core problem. Without real-time stage updates reaching the UI, the user has no feedback and perceives the system as broken.

**Independent Test**: Can be tested by triggering report generation and observing that the progress checklist updates as the server streams stage events. Each stage transition should be visible within seconds of occurring on the server.

**Acceptance Scenarios**:

1. **Given** a user clicks "Generate Idea", **When** the pipeline starts processing, **Then** the side panel displays a checklist showing all pipeline stages with the current stage marked as active (spinner) and completed stages marked with a checkmark
2. **Given** the pipeline moves from one stage to the next, **When** the server emits a stage event, **Then** the side panel updates within 2 seconds to reflect the new active stage
3. **Given** the pipeline is at the "enrichment" stage, **When** multiple data agents run in parallel, **Then** each agent (News, Fundamentals, Macro) is listed as a sub-item under "Data agents" with individual progress indicators
4. **Given** the pipeline completes, **When** the final report is ready, **Then** the progress view transitions smoothly to the full report view

---

### User Story 2 - Per-Agent Progress During Enrichment (Priority: P2)

As a user, during the enrichment phase I want to see which data agents are running, which have finished, and which are still pending — especially since agents run in parallel and some (Risk, Synthesis) run sequentially afterward.

**Why this priority**: The enrichment phase is typically the longest part of the pipeline. Without per-agent visibility, this phase appears as a single long wait.

**Independent Test**: Can be tested by enabling multiple data agents in settings, triggering generation, and observing that individual agents show active/completed states during the enrichment phase.

**Acceptance Scenarios**:

1. **Given** the enrichment phase starts with News, Fundamentals, and Macro agents enabled, **When** agents begin running in parallel, **Then** all three show active (spinner) indicators simultaneously
2. **Given** News Agent finishes before Fundamentals Agent, **When** the server reports News Agent completion, **Then** News Agent shows a checkmark while Fundamentals Agent continues showing a spinner
3. **Given** all parallel agents complete, **When** Risk Agent begins (sequential phase), **Then** Risk Agent shows a spinner while previously completed agents show checkmarks
4. **Given** only News and Fundamentals agents are enabled in settings, **When** enrichment runs, **Then** only those agents are shown in the progress sub-list (no disabled agents)

---

### User Story 3 - Graceful Error Display (Priority: P3)

As a user, if the generation fails at any stage, I want to see which stage failed and a clear error message, rather than the progress freezing with no feedback.

**Why this priority**: Error feedback is important for usability but less critical than the core progress display.

**Independent Test**: Can be tested by simulating a failure (e.g., stopping the API server mid-generation) and verifying the error is displayed with the failing stage identified.

**Acceptance Scenarios**:

1. **Given** the pipeline fails during the "thesis" stage, **When** the error event is received, **Then** the side panel shows stages up to "thesis" with the failing stage marked in red and an error message displayed below
2. **Given** a network error occurs, **When** the connection to the API server is lost, **Then** the side panel displays a meaningful error message rather than freezing on the last known stage

---

### Edge Cases

- What happens when the user navigates away from the page during generation? Progress should persist in the side panel.
- What happens when the side panel is opened after generation has already started? It should show the current progress state, not start from scratch.
- What happens when the API server sends stages out of expected order? The UI should gracefully handle unexpected stage names.
- What happens when the enrichment phase has no enabled agents? The "Data agents" stage should complete immediately without showing an empty sub-list.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The server MUST stream stage progress events to the extension in real-time as the pipeline processes each stage
- **FR-002**: The extension MUST update the side panel progress display within 2 seconds of receiving a stage event
- **FR-003**: The progress display MUST show all pipeline stages as a vertical checklist with three visual states: pending (grey), active (spinner), completed (checkmark)
- **FR-004**: During the enrichment phase, the progress display MUST show individual data agents as nested sub-items with independent progress indicators
- **FR-005**: Agents running in parallel MUST show simultaneous active (spinner) indicators
- **FR-006**: The progress display MUST transition to the full report view when the pipeline completes
- **FR-007**: If generation fails, the progress display MUST show which stage failed and display the error message
- **FR-008**: The side panel MUST correctly show current progress state when opened mid-generation (not reset to initial state)
- **FR-009**: The system MUST preserve backward compatibility — the existing popup-based "Generate" flow should continue to work alongside the floating tooltip flow

### Key Entities

- **Pipeline Stage**: A named step in the report generation process (extraction, entity, ticker, thesis, critique, confidence, enrichment, formatting). Has a status (pending, active, completed, failed).
- **Agent Progress**: A sub-item within the enrichment stage representing an individual data agent (News, Fundamentals, Risk, Macro, Synthesis). Has the same status states as a pipeline stage.
- **Stage Event**: A real-time notification from the server indicating a stage transition, containing the stage name and optional metadata (e.g., which agents are starting).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users see at least 3 distinct stage transitions during a typical report generation, providing continuous feedback that the system is working
- **SC-002**: No single stage label is displayed for more than 30 seconds without an update (stages should transition visibly, not appear stuck)
- **SC-003**: The progress view accurately reflects the server-side pipeline state with no more than 2-second lag between server event and UI update
- **SC-004**: Users can identify which specific agent is currently running during the enrichment phase
- **SC-005**: Users perceive the generation as actively working (not frozen) throughout the entire process

## Assumptions

- The server and extension are co-located on the same machine (localhost), so network latency for streaming events is negligible.
- The pipeline stages are deterministic and always execute in the same order (extraction → entity → ticker → thesis → critique → confidence → enrichment → formatting).
- Each pipeline stage takes at least 1-2 seconds, making per-stage progress meaningful (no stages so fast they're invisible).
- The enrichment phase is typically the longest, making per-agent progress especially valuable during that phase.

## Dependencies

- Depends on the existing multi-agent pipeline (002-multi-agent-data) for the stage structure and agent architecture.
- Depends on the floating tooltip feature for triggering generation from content selection.
