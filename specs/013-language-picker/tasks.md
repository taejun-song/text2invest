# Tasks: Language Picker Before Generation

**Input**: Design documents from `/specs/013-language-picker/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/, quickstart.md

**Tests**: Not explicitly requested - manual testing via extension reload workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Monorepo**: `packages/extension/src/` for Chrome Extension code
- Paths shown below use the monorepo structure from plan.md

---

## Phase 1: Setup (No New Infrastructure Needed)

**Purpose**: Verify existing infrastructure and prepare for implementation

- [x] T001 Verify `saveSettings` is exported from packages/extension/src/lib/storage.ts
- [x] T002 Confirm existing `output_language` field in UserSettings type at packages/extension/src/types/index.ts

**Checkpoint**: Existing APIs confirmed available - no new setup needed

---

## Phase 2: Foundational (Shared Constants)

**Purpose**: Add shared constants that all user stories depend on

- [x] T003 Add LANGUAGE_OPTIONS constant array after imports in packages/extension/src/sidepanel/panel.ts
- [x] T004 Add `selectedLanguage` private property to PanelController class in packages/extension/src/sidepanel/panel.ts
- [x] T005 Add `saveSettings` to import statement in packages/extension/src/sidepanel/panel.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Select Language Before Generation (Priority: P1) MVP

**Goal**: Users can see a language picker next to the Generate button and use it to select output language before generating a report.

**Independent Test**: Select text on webpage, open side panel, verify language picker appears, select Korean, generate report, verify output is in Korean.

### Implementation for User Story 1

- [x] T006 [US1] Add CSS styles for `.language-row` and `.language-select` in style block within showSelectionUI() at packages/extension/src/sidepanel/panel.ts
- [x] T007 [US1] Replace generate button HTML with language-row containing select dropdown and button in showSelectionUI() at packages/extension/src/sidepanel/panel.ts
- [x] T008 [US1] Create bindLanguagePicker() method to initialize dropdown value and bind change event in packages/extension/src/sidepanel/panel.ts
- [x] T009 [US1] Call bindLanguagePicker() at end of showSelectionUI() after DOM creation in packages/extension/src/sidepanel/panel.ts

**Checkpoint**: User Story 1 complete - language picker visible and functional with Generate button

---

## Phase 4: User Story 2 - Language Persistence Across Sessions (Priority: P2)

**Goal**: Selected language persists when browser is closed and reopened.

**Independent Test**: Select Korean language, close browser completely, reopen extension, verify picker shows Korean.

### Implementation for User Story 2

- [x] T010 [US2] Ensure bindLanguagePicker() reads output_language from getSettings() on panel open in packages/extension/src/sidepanel/panel.ts
- [x] T011 [US2] Ensure change event handler saves to storage via saveSettings() immediately in packages/extension/src/sidepanel/panel.ts

**Checkpoint**: User Story 2 complete - language persists across sessions

---

## Phase 5: User Story 3 - Auto-Detect Option (Priority: P3)

**Goal**: Auto-detect option available that uses backend language detection.

**Independent Test**: Select "Auto-detect", select Korean text, generate report, verify output matches input language.

### Implementation for User Story 3

- [x] T012 [US3] Verify "Auto-detect" is first option in LANGUAGE_OPTIONS with value 'auto' in packages/extension/src/sidepanel/panel.ts
- [x] T013 [US3] Ensure default selectedLanguage is 'auto' when no setting exists in packages/extension/src/sidepanel/panel.ts

**Checkpoint**: User Story 3 complete - Auto-detect works as default option

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [x] T014 Verify Settings page sync - changing language in panel reflects in Options page via shared storage
- [x] T015 Run quickstart.md verification checklist manually
- [x] T016 Build extension with `npm run dev` in packages/extension and test in Chrome

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - verification only
- **Foundational (Phase 2)**: Depends on Setup - adds shared constants
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed sequentially in priority order
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational (Phase 2) - Core UI implementation
- **User Story 2 (P2)**: Depends on User Story 1 - Extends persistence behavior
- **User Story 3 (P3)**: Depends on Foundational (Phase 2) - Auto-detect option (could run parallel to US1/US2)

### Within Each User Story

- CSS before HTML structure
- HTML structure before event binding
- Event binding before integration calls

### Parallel Opportunities

- T001 and T002 can run in parallel (different files, verification only)
- T003, T004, T005 must be sequential (same file)
- US1 tasks must be sequential (all modify same function)
- US2 tasks extend US1 implementation
- US3 tasks verify existing behavior (minimal code changes)

---

## Parallel Example: Setup Verification

```bash
# Launch verification tasks together:
Task: "Verify saveSettings is exported from packages/extension/src/lib/storage.ts"
Task: "Confirm existing output_language field in UserSettings type"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify existing APIs)
2. Complete Phase 2: Foundational (add constants)
3. Complete Phase 3: User Story 1 (language picker UI)
4. **STOP and VALIDATE**: Test language selection and generation
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational - Constants ready
2. Add User Story 1 - Test language selection - Deploy/Demo (MVP!)
3. Add User Story 2 - Test persistence - Deploy/Demo
4. Add User Story 3 - Test auto-detect - Deploy/Demo
5. Each story adds value without breaking previous stories

### Single Developer Strategy

Since all changes are in one file (panel.ts):
1. Complete all tasks sequentially in order
2. Build and test after each user story checkpoint
3. Estimated effort: ~50 lines of code changes

---

## Notes

- All tasks modify packages/extension/src/sidepanel/panel.ts
- No backend changes required - uses existing output_language infrastructure
- No new npm dependencies needed
- Manual testing via extension reload workflow
- Commit after each user story checkpoint for clean history
