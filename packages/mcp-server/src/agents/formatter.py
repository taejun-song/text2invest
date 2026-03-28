from datetime import datetime
from typing import Any
from uuid import uuid4

from models.agent_outputs import ConfidenceLevel, DiscoveredCompany, InferredTicker, Sector, TickerRecommendation
from models.idea_report import (
    Horizon,
    IdeaReport,
    InferredTickerReport,
    ProviderMeta,
    RationaleQuote,
    Recommendation,
    RelatedTicker,
    SectorReport,
    Signal,
    Source,
    Ticker,
    UserSettings,
)


SUMMARY_LABELS = {
    "en": {"tickers": "Tickers"},
    "ko": {"tickers": "종목"},
    "ja": {"tickers": "銘柄"},
    "zh": {"tickers": "股票代码"},
    "es": {"tickers": "Valores"},
    "fr": {"tickers": "Titres"},
    "de": {"tickers": "Wertpapiere"},
    "pt": {"tickers": "Ativos"},
    "hi": {"tickers": "टिकर"},
    "ar": {"tickers": "الأسهم"},
}

class FormatterAgent:
    name = "formatter"

    def __init__(self, settings: UserSettings, pipeline_start: datetime):
        self.settings = settings
        self.pipeline_start = pipeline_start

    def format(
        self,
        selection_text: str,
        url: str,
        title: str,
        tickers: list[dict],
        thesis: str,
        supporting_quotes: list[dict],
        catalysts: list[str],
        horizon: str,
        risks: list[str],
        counter_thesis: str,
        confidence_score: float,
        confidence_explanation: str,
        limitations: list[str],
        enrichment: dict[str, Any] | None = None,
        communication_log: Any | None = None,
        recommendations: dict[str, TickerRecommendation] | None = None,
        discovered_companies: list[DiscoveredCompany] | None = None,
        search_depth: str | None = None,
        sectors: list[Sector] | None = None,
        inferred_tickers: list[InferredTicker] | None = None,
    ) -> IdeaReport:
        pipeline_duration_ms = int((datetime.now() - self.pipeline_start).total_seconds() * 1000)

        formatted_tickers = []
        for t in tickers:
            rec = None
            if recommendations and t["symbol"] in recommendations:
                r = recommendations[t["symbol"]]
                rec = Recommendation(
                    signal=Signal(r.signal),
                    certainty=r.certainty,
                    rationale=r.rationale,
                    factors=r.factors,
                )
            formatted_tickers.append(Ticker(
                symbol=t["symbol"],
                company_name=t.get("company", t["symbol"]),
                confidence=t["confidence"],
                recommendation=rec,
            ))

        formatted_quotes = [
            RationaleQuote(
                quote=q["quote"],
                start_offset=q["start_offset"],
                end_offset=q["end_offset"],
            )
            for q in supporting_quotes
        ]

        executive_summary = self._generate_executive_summary(thesis, formatted_tickers)

        # Build enrichment fields
        news_context = None
        fundamentals_summary = None
        cross_reference_analysis = None
        macro_context = None
        agent_attributions = None

        if enrichment:
            news_output = enrichment.get("news_context")
            if news_output:
                news_context = [item.model_dump() for item in news_output.news_items]

            fund_output = enrichment.get("fundamentals_summary")
            if fund_output:
                fundamentals_summary = [snap.model_dump() for snap in fund_output.snapshots]

            synthesis = enrichment.get("synthesis")
            if synthesis:
                if synthesis.cross_reference:
                    cross_reference_analysis = synthesis.cross_reference.model_dump()
                agent_attributions = synthesis.agent_attributions or None

            macro_output = enrichment.get("macro_context")
            if macro_output:
                if hasattr(macro_output, "context") and macro_output.context:
                    macro_context = macro_output.context.model_dump()
                elif hasattr(macro_output, "model_dump"):
                    macro_context = macro_output.model_dump()

        quantitative_data = self._build_quantitative_data(fundamentals_summary)
        comm_log_data = None
        if communication_log:
            comm_log_data = communication_log.model_dump()

        formatted_related: list[RelatedTicker] = []
        if discovered_companies:
            for c in discovered_companies:
                rec = None
                if recommendations and c.symbol in recommendations:
                    r = recommendations[c.symbol]
                    rec = Recommendation(
                        signal=Signal(r.signal),
                        certainty=r.certainty,
                        rationale=r.rationale,
                        factors=r.factors,
                    )
                rel = c.relationship
                if isinstance(rel, str):
                    from models.idea_report import Relationship
                    rel = Relationship(rel)
                formatted_related.append(RelatedTicker(
                    symbol=c.symbol,
                    company_name=c.company_name,
                    relationship=rel,
                    primary_symbol=c.primary_symbol,
                    depth=c.depth,
                    recommendation=rec,
                ))

        formatted_sectors: list[SectorReport] = []
        if sectors:
            for s in sectors:
                conf = s.confidence.value if isinstance(s.confidence, ConfidenceLevel) else s.confidence
                formatted_sectors.append(SectorReport(
                    name=s.name,
                    confidence=conf,
                    sub_sectors=s.sub_sectors,
                ))

        formatted_inferred: list[InferredTickerReport] = []
        if inferred_tickers:
            for t in inferred_tickers:
                conf = t.confidence.value if isinstance(t.confidence, ConfidenceLevel) else t.confidence
                formatted_inferred.append(InferredTickerReport(
                    symbol=t.symbol,
                    company_name=t.company_name,
                    sector=t.sector,
                    relevance_explanation=t.relevance_explanation,
                    confidence=conf,
                    market_cap_tier=t.market_cap_tier,
                    supply_chain_layer=t.supply_chain_layer,
                    verified=t.verified,
                ))

        return IdeaReport(
            id=uuid4(),
            created_at=datetime.now(),
            source=Source(url=url, title=title),
            selection_text=selection_text,
            tickers=formatted_tickers,
            thesis=thesis,
            executive_summary=executive_summary,
            rationale_quotes=formatted_quotes,
            catalysts=catalysts,
            risks=risks,
            counter_thesis=counter_thesis,
            horizon=Horizon(horizon),
            confidence_score=None,
            confidence_explanation=None,
            quantitative_data=quantitative_data,
            limitations=limitations,
            provider_meta=ProviderMeta(
                provider=self.settings.provider,
                model=self.settings.model,
                temperature=self.settings.temperature,
                pipeline_duration_ms=pipeline_duration_ms,
            ),
            news_context=news_context,
            fundamentals_summary=fundamentals_summary,
            cross_reference_analysis=cross_reference_analysis,
            macro_context=macro_context,
            agent_attributions=agent_attributions,
            communication_log=comm_log_data,
            related_tickers=formatted_related,
            search_depth=search_depth,
            sectors=formatted_sectors,
            inferred_tickers=formatted_inferred,
        )

    def _generate_executive_summary(self, thesis: str, tickers: list[Ticker]) -> list[str]:
        lang = self.settings.output_language
        if not lang or lang == "auto":
            lang = "en"
        labels = SUMMARY_LABELS.get(lang, SUMMARY_LABELS["en"])
        summary = []
        if tickers:
            ticker_str = ", ".join(t.symbol for t in tickers[:3])
            summary.append(f"{labels['tickers']}: {ticker_str}")
        thesis_short = thesis[:200] + "..." if len(thesis) > 200 else thesis
        summary.append(thesis_short)
        return summary[:3]

    def _build_quantitative_data(self, fundamentals_summary: list | None) -> list:
        if not fundamentals_summary:
            return []
        quantitative = []
        for snap in fundamentals_summary:
            ticker = snap.get("ticker", "")
            tech = snap.get("technical_indicators")
            fund = snap.get("fundamental_data", {})
            metrics = fund.get("metrics", {}) if fund else {}
            entry = {
                "ticker": ticker,
                "company_name": snap.get("company_name", ""),
                "fundamentals": {
                    "pe_ratio": metrics.get("pe_ratio"),
                    "market_cap": metrics.get("market_cap"),
                    "revenue": metrics.get("revenue"),
                    "profit_margin": metrics.get("profit_margin"),
                    "dividend_yield": metrics.get("dividend_yield"),
                    "eps": metrics.get("eps"),
                },
                "technicals": None,
            }
            if tech:
                entry["technicals"] = {
                    "current_price": tech.get("current_price"),
                    "ma_50": tech.get("ma_50"),
                    "ma_200": tech.get("ma_200"),
                    "rsi_14": tech.get("rsi_14"),
                    "price_change_1w": tech.get("price_change_1w"),
                    "price_change_1m": tech.get("price_change_1m"),
                    "price_change_3m": tech.get("price_change_3m"),
                }
            quantitative.append(entry)
        return quantitative
