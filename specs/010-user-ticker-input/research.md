# Research: User Ticker Input

## Decision 1: Chip/Tag Component Implementation

**Decision**: Implement a custom chip component using vanilla TypeScript and CSS, consistent with existing panel styling.

**Rationale**:
- No external UI library is used in the extension; adding one would increase bundle size
- The existing panel.ts already uses manual DOM manipulation patterns
- Chip component is simple enough to implement in ~50 lines of code
- Maintains consistency with existing visual style

**Alternatives Considered**:
- External library (e.g., tagify): Rejected due to bundle size and style mismatch
- Web Components: Overkill for single-use component; adds complexity

## Decision 2: Input Trigger for Adding Chips

**Decision**: Add ticker as chip when user presses Enter, comma, or Tab key; also on blur.

**Rationale**:
- Enter is the most intuitive action for "submit this ticker"
- Comma matches mental model of "comma-separated" even though display is chips
- Tab allows keyboard-only workflow
- Blur ensures partially-typed ticker is captured when clicking Generate

**Alternatives Considered**:
- Only on Enter: Would lose partially-typed input on button click
- Explicit "Add" button: Adds extra click; chips UI is standard enough

## Decision 3: Validation Timing

**Decision**: Validate on chip creation (not keystroke-by-keystroke). Show error chip style for invalid tickers.

**Rationale**:
- Per-keystroke validation would be noisy during typing (e.g., "A" alone is invalid but could become "AAPL")
- Showing invalid chip with distinct style gives clear feedback without blocking typing flow
- User can remove invalid chip by clicking X

**Alternatives Considered**:
- Block invalid input: Poor UX; user can't even type to see what's wrong
- Validate only on Generate: Late feedback; user has to wait for generation to fail

## Decision 4: User Ticker Indicator in Report

**Decision**: Add "(user)" suffix to user-provided tickers in the report ticker display, with distinct CSS styling.

**Rationale**:
- Must be distinguishable per SC-004
- Simple text suffix is clear and doesn't require new UI patterns
- CSS class allows visual distinction (e.g., lighter color, italic)

**Alternatives Considered**:
- Separate section: Overcomplicates report layout
- Icon indicator: Requires additional assets; text suffix is simpler

## Decision 5: State Management for Ticker Input

**Decision**: Store tickers as array in panel controller state; do not persist to chrome.storage.

**Rationale**:
- Tickers are contextual to the current selection/generation
- Persisting would create confusing state if user selects different text
- Clear on successful generation or navigation away

**Alternatives Considered**:
- Persist recent tickers: Adds complexity; unclear UX benefit
- Use chrome.storage.session: Session storage doesn't survive service worker restart

## Decision 6: Message Passing Updates

**Decision**: Add `user_tickers` field to GENERATE message payload in service-worker.ts.

**Rationale**:
- Follows existing message passing pattern
- Minimal change to existing flow
- Backend already expects this parameter

**Alternatives Considered**:
- Separate message type: Overcomplicates for no benefit
- Direct API call from panel: Would bypass service worker architecture
