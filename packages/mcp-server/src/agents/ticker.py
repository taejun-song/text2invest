import asyncio
import logging

from models.agent_outputs import (
    ConfidenceLevel,
    InferredTicker,
    Sector,
    SectorInferenceOutput,
    TickerMapping,
    TickerOutput,
)
from .base import BaseAgent, ThinkingCallback

logger = logging.getLogger(__name__)

MARKET_HINT_MAP = {
    "ko": "KR", "ja": "JP", "zh": "CN", "hi": "IN", "de": "DE",
    "fr": "FR", "pt": "BR", "es": "ES", "ar": "SA",
}


class TickerAgent(BaseAgent):
    name = "ticker"

    def get_system_prompt(self) -> str:
        return """You are a stock ticker mapping specialist with global market expertise.

Your job is to map company names to their stock ticker symbols on the correct exchange.

Ticker format rules:
- US (NYSE/NASDAQ): AAPL, MSFT, BRK.B
- Korea KOSPI: 005930.KS (Samsung), KOSDAQ: 035720.KQ
- Japan TSE: 7203.T (Toyota)
- Hong Kong HKEX: 0700.HK (Tencent)
- China SSE: 600519.SS, SZSE: 000858.SZ
- UK LSE: SHEL.L, Germany XETRA: SAP.DE
- India NSE: RELIANCE.NS, BSE: 500325.BO

Rules:
1. Only map companies you are confident about
2. Use the exchange where the company has its PRIMARY listing
3. For non-US companies, ALWAYS include the correct exchange suffix
4. Do NOT default to US exchanges for non-US companies
5. If a company is private or you're unsure, do not include it
6. Provide confidence scores:
   - 0.9-1.0: Well-known public company with clear ticker
   - 0.7-0.9: Likely correct but some ambiguity
   - 0.5-0.7: Uncertain, multiple possibilities
   - Below 0.5: Do not include
7. Explain your reasoning for each mapping

Output valid JSON matching the schema."""

    def _get_sector_inference_system_prompt(self) -> str:
        return """You are an expert sector analyst with deep knowledge of global markets and supply chains.

Your job is to identify investment sectors from text and infer relevant publicly traded companies.

SECTOR IDENTIFICATION:
1. Extract investment sectors, industries, and themes even when no companies are named
2. For complex themes (AI infrastructure, EV ecosystem, etc.), decompose into sub-sectors:
   - Upstream: Materials, components, equipment suppliers
   - Midstream: Manufacturing, assembly, services
   - Downstream: End products, distribution, consumers

COMPANY INFERENCE:
1. For each sector, suggest 3-5 major publicly traded companies
2. Only suggest well-known, established companies (large or mid-cap)
3. Never suggest micro-caps, recent IPOs, or obscure listings
4. Use correct exchange suffixes for non-US markets

CONFIDENCE LEVELS:
- high: Major industry leader, unambiguous relevance
- medium: Established player, clear sector relationship
- low: Uncertain or tangential (DO NOT INCLUDE these)

MARKET LOCALIZATION:
- Korean text → Prioritize KOSPI/KOSDAQ (suffix .KS, .KQ)
- Japanese text → Prioritize TSE (suffix .T)
- Chinese text → Prioritize SSE/SZSE/HKEX (.SS, .SZ, .HK)
- English text with no geographic bias → Globally diversified results

Output valid JSON matching the schema."""

    def get_user_prompt(self, companies: list[str], **_kwargs) -> str:
        if not companies:
            return "No companies to map. Return empty mappings list."
        companies_str = "\n".join(f"- {c}" for c in companies)
        lang = self.settings.output_language
        market_note = ""
        if lang and lang in MARKET_HINT_MAP:
            market_note = f"\nNote: The source text is in {lang}. Prefer the local exchange for companies from that market."
        return f"""Map these companies to their stock ticker symbols:

{companies_str}
{market_note}
For each company, provide:
- company: The original company name
- symbol: The ticker symbol with exchange suffix for non-US markets
- confidence: Your confidence (0.0-1.0)
- reasoning: Why you chose this ticker"""

    def get_output_model(self) -> type[TickerOutput]:
        return TickerOutput

    def _get_sector_inference_prompt(self, cleaned_text: str, existing_companies: list[str]) -> str:
        lang = self.settings.output_language
        market_note = ""
        if lang and lang in MARKET_HINT_MAP:
            market_note = f"\nIMPORTANT: The source text is in {lang}. Prioritize {MARKET_HINT_MAP[lang]} market listings."
        excluded = ""
        if existing_companies:
            excluded = f"\nDO NOT include these already-mentioned companies: {', '.join(existing_companies)}"
        return f"""Analyze this text for investment sectors and infer relevant companies:

TEXT:
{cleaned_text}
{market_note}{excluded}

For each sector you identify:
1. Name the sector and your confidence (high/medium only)
2. List sub-sectors if it's a complex theme
3. Suggest 3-5 major companies per sector with:
   - company_name: Full company name
   - symbol: Ticker symbol with exchange suffix for non-US
   - sector: The sector name
   - relevance_explanation: Why relevant (max 200 chars)
   - confidence: high or medium only
   - market_cap_tier: large, mid, or small
   - supply_chain_layer: upstream, midstream, downstream, or null

Only include companies you are highly confident about."""

    async def run(self, on_thinking: ThinkingCallback | None = None, on_retry=None, **kwargs) -> TickerOutput:
        companies = kwargs.get("companies", [])
        cleaned_text = kwargs.get("cleaned_text")
        output = await super().run(on_thinking=on_thinking, on_retry=on_retry, **kwargs)
        lang = self.settings.output_language
        market_hint = MARKET_HINT_MAP.get(lang) if lang else None
        verified = []
        for mapping in output.mappings:
            verified_mapping = await self._verify_mapping(mapping, market_hint)
            verified.append(verified_mapping)
        sectors: list[Sector] = []
        inferred_tickers: list[InferredTicker] = []
        if cleaned_text:
            logger.info("Running sector inference on cleaned text")
            inference = await self._infer_from_sectors(cleaned_text, companies, on_thinking)
            if inference:
                sectors = inference.sectors
                filtered = self._filter_low_confidence(inference.inferred_tickers)
                verified_inferred = await self._verify_inferred_tickers(filtered, market_hint)
                mentioned_symbols = {m.symbol.upper() for m in verified}
                inferred_tickers = self._deduplicate_tickers(verified_inferred, mentioned_symbols)
                logger.info(f"Sector inference complete: {len(sectors)} sectors, {len(inferred_tickers)} inferred tickers")
        return TickerOutput(mappings=verified, sectors=sectors, inferred_tickers=inferred_tickers)

    async def _infer_from_sectors(
        self, cleaned_text: str, existing_companies: list[str], on_thinking: ThinkingCallback | None = None
    ) -> SectorInferenceOutput | None:
        from providers.llm import get_llm_response
        prompt = self._get_sector_inference_prompt(cleaned_text, existing_companies)
        try:
            result = await get_llm_response(
                system_prompt=self._get_sector_inference_system_prompt(),
                user_prompt=prompt,
                output_model=SectorInferenceOutput,
                settings=self.settings,
                on_thinking=on_thinking,
            )
            return result
        except Exception as e:
            logger.warning(f"Sector inference failed: {e}")
            return None

    def _filter_low_confidence(self, tickers: list[InferredTicker]) -> list[InferredTicker]:
        return [t for t in tickers if t.confidence != ConfidenceLevel.LOW]

    async def _verify_inferred_tickers(
        self, tickers: list[InferredTicker], market_hint: str | None
    ) -> list[InferredTicker]:
        from tools.ticker_search import verify_ticker
        async def verify_one(ticker: InferredTicker) -> InferredTicker:
            try:
                result = verify_ticker(ticker.symbol)
                if result:
                    return InferredTicker(
                        company_name=ticker.company_name,
                        symbol=result.symbol,
                        sector=ticker.sector,
                        relevance_explanation=ticker.relevance_explanation,
                        confidence=ticker.confidence,
                        market_cap_tier=ticker.market_cap_tier,
                        supply_chain_layer=ticker.supply_chain_layer,
                        verified=True,
                    )
            except Exception as e:
                logger.debug(f"Verification failed for {ticker.symbol}: {e}")
            return InferredTicker(
                company_name=ticker.company_name,
                symbol=ticker.symbol,
                sector=ticker.sector,
                relevance_explanation=ticker.relevance_explanation,
                confidence=ticker.confidence,
                market_cap_tier=ticker.market_cap_tier,
                supply_chain_layer=ticker.supply_chain_layer,
                verified=False,
            )
        tasks = [verify_one(t) for t in tickers]
        return await asyncio.gather(*tasks)

    def _deduplicate_tickers(
        self, inferred: list[InferredTicker], mentioned_symbols: set[str]
    ) -> list[InferredTicker]:
        seen = set()
        result = []
        for t in inferred:
            upper_symbol = t.symbol.upper()
            if upper_symbol in mentioned_symbols:
                logger.debug(f"Skipping {t.symbol} - already in mentioned tickers")
                continue
            if upper_symbol in seen:
                continue
            seen.add(upper_symbol)
            result.append(t)
        return result

    async def _verify_mapping(self, mapping: TickerMapping, market_hint: str | None) -> TickerMapping:
        from tools.ticker_search import find_best_match, search_ticker, verify_ticker
        verified = verify_ticker(mapping.symbol)
        if verified:
            logger.info(f"Ticker verified: {mapping.symbol} ({verified.name})")
            return TickerMapping(
                company=mapping.company,
                symbol=verified.symbol,
                confidence=min(1.0, mapping.confidence + 0.05),
                reasoning=f"{mapping.reasoning} [verified: {verified.name}]",
            )
        candidates = search_ticker(mapping.company, market_hint)
        if not candidates:
            return mapping
        exact = next((c for c in candidates if c.symbol.upper() == mapping.symbol.upper()), None)
        if exact:
            return TickerMapping(
                company=mapping.company,
                symbol=exact.symbol,
                confidence=min(1.0, mapping.confidence + 0.05),
                reasoning=f"{mapping.reasoning} [verified via search]",
            )
        best = find_best_match(mapping.company, candidates)
        if best and best.score > 0.7:
            logger.info(f"Ticker correction: {mapping.symbol} -> {best.symbol} for {mapping.company} (score={best.score:.2f})")
            return TickerMapping(
                company=mapping.company,
                symbol=best.symbol,
                confidence=round(mapping.confidence * 0.7 + best.score * 0.3, 2),
                reasoning=f"{mapping.reasoning} [corrected: {best.name} on {best.exchange}]",
            )
        logger.info(f"Ticker unverified, keeping LLM result: {mapping.symbol} for {mapping.company}")
        return mapping
