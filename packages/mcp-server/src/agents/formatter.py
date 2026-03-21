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
    "en": {"tickers": "Tickers", "confidence": "Confidence"},
    "ko": {"tickers": "종목", "confidence": "신뢰도"},
    "ja": {"tickers": "銘柄", "confidence": "信頼度"},
    "zh": {"tickers": "股票代码", "confidence": "置信度"},
    "es": {"tickers": "Valores", "confidence": "Confianza"},
    "fr": {"tickers": "Titres", "confidence": "Confiance"},
    "de": {"tickers": "Wertpapiere", "confidence": "Konfidenz"},
    "pt": {"tickers": "Ativos", "confidence": "Confianca"},
    "hi": {"tickers": "टिकर", "confidence": "विश्वास"},
    "ar": {"tickers": "الأسهم", "confidence": "الثقة"},
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

        executive_summary = self._generate_executive_summary(
            thesis, formatted_tickers, confidence_score
        )

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
            confidence_score=confidence_score,
            confidence_explanation=confidence_explanation,
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

    def _generate_executive_summary(
        self, thesis: str, tickers: list[Ticker], confidence: float
    ) -> list[str]:
        lang = self.settings.output_language
        if not lang or lang == "auto":
            lang = "en"
        labels = SUMMARY_LABELS.get(lang, SUMMARY_LABELS["en"])
        summary = []
        if tickers:
            ticker_str = ", ".join(t.symbol for t in tickers[:3])
            summary.append(f"{labels['tickers']}: {ticker_str}")
        thesis_short = thesis[:150] + "..." if len(thesis) > 150 else thesis
        summary.append(thesis_short)
        summary.append(f"{labels['confidence']}: {confidence:.0%}")
        return summary[:3]
