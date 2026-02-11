from datetime import datetime

from ..models.idea_report import IdeaReport, UserSettings
from .confidence import ConfidenceAgent
from .critique import CritiqueAgent
from .entity import EntityAgent
from .extraction import ExtractionAgent
from .formatter import FormatterAgent
from .thesis import ThesisAgent
from .ticker import TickerAgent


class Pipeline:
    def __init__(self, settings: UserSettings):
        self.settings = settings

    async def run(
        self,
        selection_text: str,
        url: str,
        title: str,
        on_stage: callable = None,
    ) -> IdeaReport:
        pipeline_start = datetime.now()

        if on_stage:
            on_stage("extraction")
        extraction_agent = ExtractionAgent(self.settings)
        extraction_output = await extraction_agent.run(text=selection_text)

        if on_stage:
            on_stage("entity")
        entity_agent = EntityAgent(self.settings)
        entity_output = await entity_agent.run(cleaned_text=extraction_output.cleaned_text)

        if on_stage:
            on_stage("ticker")
        ticker_agent = TickerAgent(self.settings)
        ticker_output = await ticker_agent.run(companies=entity_output.companies)

        tickers_for_thesis = [t.symbol for t in ticker_output.mappings]

        if on_stage:
            on_stage("thesis")
        thesis_agent = ThesisAgent(self.settings)
        thesis_output = await thesis_agent.run(
            cleaned_text=extraction_output.cleaned_text,
            companies=entity_output.companies,
            tickers=tickers_for_thesis,
        )

        if on_stage:
            on_stage("critique")
        critique_agent = CritiqueAgent(self.settings)
        critique_output = await critique_agent.run(
            thesis=thesis_output.thesis,
            cleaned_text=extraction_output.cleaned_text,
            companies=entity_output.companies,
        )

        tickers_for_confidence = [
            {"symbol": t.symbol, "confidence": t.confidence} for t in ticker_output.mappings
        ]

        if on_stage:
            on_stage("confidence")
        confidence_agent = ConfidenceAgent(self.settings)
        confidence_output = await confidence_agent.run(
            thesis=thesis_output.thesis,
            risks=critique_output.risks,
            counter_thesis=critique_output.counter_thesis,
            missing_info=critique_output.missing_info,
            tickers=tickers_for_confidence,
        )

        if on_stage:
            on_stage("formatting")
        formatter = FormatterAgent(self.settings, pipeline_start)

        tickers_for_formatter = [
            {
                "symbol": t.symbol,
                "company": t.company,
                "confidence": t.confidence,
            }
            for t in ticker_output.mappings
        ]

        quotes_for_formatter = [
            {
                "quote": q.quote,
                "start_offset": q.start_offset,
                "end_offset": q.end_offset,
            }
            for q in thesis_output.supporting_quotes
        ]

        return formatter.format(
            selection_text=selection_text,
            url=url,
            title=title,
            tickers=tickers_for_formatter,
            thesis=thesis_output.thesis,
            supporting_quotes=quotes_for_formatter,
            catalysts=thesis_output.catalysts,
            horizon=thesis_output.horizon.value,
            risks=critique_output.risks,
            counter_thesis=critique_output.counter_thesis,
            confidence_score=confidence_output.score,
            confidence_explanation=confidence_output.explanation,
            limitations=confidence_output.limitations,
        )
