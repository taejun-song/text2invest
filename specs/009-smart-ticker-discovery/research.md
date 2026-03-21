# Research: Smart Ticker Discovery

**Feature**: 009-smart-ticker-discovery
**Date**: 2026-03-21

## Research Questions

### 1. How to structure LLM prompt for sector identification + company inference?

**Decision**: Single combined prompt that extracts sectors AND infers companies in one call.

**Rationale**:
- Minimizes latency by avoiding sequential LLM calls
- LLM can use sector context directly when inferring companies
- Matches existing agent pattern (single prompt → structured output)
- Keeps within the 30% latency budget

**Alternatives Considered**:
- Two-step (sector first, then companies): Rejected — doubles latency, no accuracy benefit
- Parallel calls: Rejected — inference depends on sector context

### 2. What output schema supports both mentioned and inferred tickers?

**Decision**: Extend `TickerOutput` with a new `inferred_tickers` field containing `InferredTicker` objects, keeping existing `mappings` for directly mentioned companies.

**Rationale**:
- Backward compatible — existing `mappings` unchanged
- Clear separation per FR-006 (distinguish mentioned vs inferred)
- Each `InferredTicker` carries sector, explanation, confidence (high/medium/low)

**Alternatives Considered**:
- Single list with source flag: Rejected — harder to process, mixes concerns
- Separate SectorInferenceOutput: Rejected — requires pipeline changes, adds complexity

### 3. How to handle confidence levels (high/medium/low)?

**Decision**: Use enum-based confidence levels in Pydantic model, filtered at output time (exclude "low").

**Rationale**:
- Matches clarification decision (qualitative over numeric)
- LLM can reliably assign categorical confidence
- Simple filter: `if confidence != "low"`

**Alternatives Considered**:
- Numeric 0-1 with threshold: Rejected per clarification decision
- No filtering (return all): Rejected per FR-010

### 4. How to integrate sector inference into existing TickerAgent flow?

**Decision**: Add sector inference as a parallel concern within TickerAgent.run(), executed before or alongside company-to-ticker mapping.

**Rationale**:
- Clarification confirmed: extend TickerAgent, not new agent
- Can run sector inference with minimal text (cleaned_text input)
- Verification uses existing ticker_search.py tools

**Implementation Approach**:
1. TickerAgent receives `cleaned_text` in addition to `companies` list
2. If text provided, run sector inference prompt
3. Verify inferred tickers via yfinance (with unverified flag if fails)
4. Combine with existing company-to-ticker mappings
5. Deduplicate per FR-009

### 5. How to prioritize local-exchange tickers for non-English text?

**Decision**: Pass detected language to sector inference prompt as market context hint.

**Rationale**:
- Already implemented in current TickerAgent (MARKET_HINT_MAP)
- LLM can weight local companies higher when language hint provided
- yfinance search already accepts market_hint parameter

**Alternatives Considered**:
- Post-processing reordering: Rejected — better to get it right in inference
- Separate locale-specific prompts: Rejected — over-engineered

### 6. How to handle yfinance failures gracefully?

**Decision**: Per clarification — return ticker with `verified: false` flag, don't exclude.

**Rationale**:
- User sees all inferred tickers
- Verification status clearly communicated
- System doesn't fail silently

**Implementation**:
- Try `verify_ticker()` for each inferred ticker
- If fails (timeout, rate limit, not found): set `verified=False`
- If succeeds: set `verified=True`, update symbol if corrected

### 7. How to decompose complex themes into sub-sectors?

**Decision**: Include supply chain decomposition in the sector inference prompt, returning multiple sectors when applicable.

**Rationale**:
- FR-008 requires sub-sector decomposition for themes like "AI infrastructure"
- SC-006 requires spanning 2+ supply chain layers
- Single prompt can identify: sector, sub-sectors, and companies per layer

**Prompt Structure**:
```
Identify sectors and key companies from this text:
- Primary sector(s)
- Sub-sectors/supply chain layers (if complex theme)
- Top 3-5 companies per sector with ticker, exchange, and relevance
```

## Technical Decisions

| Decision | Choice | Impact |
|----------|--------|--------|
| Prompt strategy | Single combined call | Low latency |
| Output model | Extended TickerOutput + InferredTicker | Backward compatible |
| Confidence model | Enum (high/medium/low) | Clear filtering |
| Integration point | TickerAgent.run() | Minimal pipeline changes |
| Locale handling | Language hint in prompt | Leverages existing pattern |
| Verification failure | Unverified flag | Graceful degradation |
| Sub-sector handling | Multi-sector prompt output | Comprehensive coverage |

## Dependencies

- **yfinance**: Already in use, no changes needed
- **LiteLLM**: Already in use, no changes needed
- **Pydantic**: Already in use, add new models

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| LLM inference quality varies | Medium | Use established companies only, verify with yfinance |
| Latency exceeds 30% budget | Low | Single prompt, parallel verification calls |
| Hallucinated tickers | Medium | yfinance verification catches most, unverified flag for rest |
| Non-English ticker formats | Low | MARKET_HINT_MAP already handles major exchanges |
