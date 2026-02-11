from datetime import datetime
from uuid import uuid4

from ..models.idea_report import (
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
