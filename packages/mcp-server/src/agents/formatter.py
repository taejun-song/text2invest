from datetime import datetime
from typing import Any
from uuid import uuid4

from models.idea_report import (
    Horizon,
    IdeaReport,
    ProviderMeta,
    RationaleQuote,
    Source,
    Ticker,
    UserSettings,
)


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
    ) -> IdeaReport:
        pipeline_duration_ms = int((datetime.now() - self.pipeline_start).total_seconds() * 1000)

        formatted_tickers = [
            Ticker(
                symbol=t["symbol"],
                company_name=t.get("company", t["symbol"]),
                confidence=t["confidence"],
            )
            for t in tickers
        ]

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
        )

    def _generate_executive_summary(
        self, thesis: str, tickers: list[Ticker], confidence: float
    ) -> list[str]:
        summary = []
        if tickers:
            ticker_str = ", ".join(t.symbol for t in tickers[:3])
            summary.append(f"Tickers: {ticker_str}")
        thesis_short = thesis[:150] + "..." if len(thesis) > 150 else thesis
        summary.append(thesis_short)
        summary.append(f"Confidence: {confidence:.0%}")
        return summary[:3]
