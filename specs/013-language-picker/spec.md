# Feature Specification: Language Picker Before Generation

**Feature Branch**: `013-language-picker`
**Created**: 2026-03-28
**Status**: Draft
**Input**: User description: "I want to set the language before we generate idea"

## Clarifications

### Session 2026-03-28

- Q: Where should the language picker be positioned relative to other UI elements? → A: Language picker should be placed with/near the Generate Idea button

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select Language Before Generation (Priority: P1)

A user wants to generate an investment analysis report in a specific language. Before clicking the Generate button, they select their preferred output language from a visible dropdown/selector in the side panel. The generated report is then produced in that language.

**Why this priority**: This is the core feature - users need an accessible way to choose language before generation rather than navigating to settings.

**Independent Test**: Can be tested by selecting text, choosing a language from the picker, generating a report, and verifying the output is in the selected language.

**Acceptance Scenarios**:

1. **Given** the user has selected text on a webpage, **When** they open the side panel, **Then** they see a language selection control near the Generate button
2. **Given** the user selects "Korean" from the language picker, **When** they click Generate, **Then** the resulting report is generated in Korean
3. **Given** the user selects "Japanese" and generates a report, **When** they later select new text without changing the language, **Then** the next generation also uses Japanese

---

### User Story 2 - Language Persistence Across Sessions (Priority: P2)

A user who regularly reads content in Korean wants their language preference to persist. After selecting Korean once, subsequent sessions should default to Korean without requiring re-selection.

**Why this priority**: Reduces friction for regular users who consistently want reports in the same language.

**Independent Test**: Can be tested by selecting a language, closing the browser, reopening, and verifying the language picker shows the previously selected language.

**Acceptance Scenarios**:

1. **Given** the user has previously selected "Korean" as their language, **When** they open the extension in a new session, **Then** the language picker shows "Korean" as the selected option
2. **Given** the user changes language from "Korean" to "English", **When** they close and reopen the panel, **Then** "English" is shown as selected

---

### User Story 3 - Auto-Detect Option (Priority: P3)

A multilingual user wants the system to automatically detect the appropriate language based on the selected text content. They choose "Auto-detect" in the picker, and the system determines the output language from the input text.

**Why this priority**: Provides convenience for users who work with content in multiple languages and want output to match input.

**Independent Test**: Can be tested by selecting "Auto-detect", selecting Korean text, generating, and verifying output is in Korean.

**Acceptance Scenarios**:

1. **Given** the user selects "Auto-detect" option, **When** they select Korean text and generate, **Then** the report is generated in Korean
2. **Given** the user selects "Auto-detect" option, **When** they select English text and generate, **Then** the report is generated in English

---

### Edge Cases

- What happens when the user changes language mid-generation? The in-progress generation continues with its original language setting
- How does auto-detect handle mixed-language text? Uses the dominant language detected in the text
- What happens if an unsupported language is detected? Falls back to English with a notification

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a language selection control alongside the Generate Idea button in the side panel
- **FR-002**: System MUST show the language picker only when the Generate Idea button is visible (i.e., when text is selected)
- **FR-003**: System MUST include an "Auto-detect" option that derives language from input text
- **FR-004**: System MUST support the same languages currently available in Settings (English, Korean, Japanese, Chinese, Spanish, French, German, Portuguese, Hindi, Arabic)
- **FR-005**: System MUST persist the selected language preference across browser sessions
- **FR-006**: System MUST sync the language picker selection with the Settings page language preference
- **FR-007**: System MUST apply the selected language to all generated report content including thesis, risks, catalysts, and recommendations
- **FR-008**: System MUST NOT require navigation to Settings to change language before generation

### Key Entities

- **Language Preference**: The user's selected output language (code, display name, auto-detect flag)
- **User Settings**: Extended to include quick-access language preference that syncs with the existing output_language setting

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can select their preferred language and generate a report in under 5 seconds (no navigation to Settings required)
- **SC-002**: Language selection persists correctly in 100% of browser sessions
- **SC-003**: Auto-detect correctly identifies the input language for single-language text in 95% of cases
- **SC-004**: Generated reports contain content exclusively in the selected language (no language mixing)

## Assumptions

- The existing language infrastructure in the backend (output_language setting) is fully functional and supports all listed languages
- The side panel has sufficient vertical space to accommodate an additional UI element
- Users understand language codes or display names shown in the picker
- The current Settings page language selector will remain but be synced with the new picker

## Out of Scope

- Adding new languages beyond those currently supported
- Language-specific formatting (e.g., right-to-left for Arabic)
- Translation of previously generated reports
- Per-report language tracking in report history
