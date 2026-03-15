import json
import logging
from datetime import datetime

from models.idea_report import IdeaReport, UserSettings
from .confidence import ConfidenceAgent
from .critique import CritiqueAgent
from .entity import EntityAgent
from .extraction import ExtractionAgent
from .formatter import FormatterAgent
from .thesis import ThesisAgent
from .ticker import TickerAgent

logger = logging.getLogger(__name__)


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

        # Collaborative enrichment phase
        enrichment = {}
        communication_log = None

        if self._should_run_collaborative():
            if on_stage:
                on_stage("enrichment")
            try:
                enrichment, communication_log = await self._run_collaborative(
                    tickers=tickers_for_thesis,
                    companies=entity_output.companies,
                    thesis=thesis_output.thesis,
                    executive_summary=[],
                    risks=critique_output.risks,
                )
            except Exception as e:
                logger.warning(f"Collaborative enrichment failed, returning text-only report: {e}")

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
            enrichment=enrichment,
            communication_log=communication_log,
        )

    def _should_run_collaborative(self) -> bool:
        if not self.settings.agent_configs:
            return False
        for cfg in self.settings.agent_configs:
            enabled = cfg.get("enabled", True) if isinstance(cfg, dict) else cfg.enabled
            if enabled:
                return True
        return False

    async def _run_collaborative(
        self,
        tickers: list[str],
        companies: list[str],
        thesis: str,
        executive_summary: list[str],
        risks: list[str],
    ) -> tuple[dict, object]:
        from .collaborative.coordinator import Coordinator
        from .collaborative.fundamentals import FundamentalsAgent
        from .collaborative.macro import MacroAgent
        from .collaborative.news import NewsAgent
        from .collaborative.risk import RiskAgent
        from .collaborative.synthesis import SynthesisAgent

        coordinator = Coordinator(self.settings)

        data_agents = []
        if coordinator.is_agent_enabled("news_agent"):
            data_agents.append(NewsAgent(
                self.settings,
                use_external_data=coordinator.should_use_external_data("news_agent"),
            ))
        if coordinator.is_agent_enabled("fundamentals_agent") and (tickers or companies):
            data_agents.append(FundamentalsAgent(
                self.settings,
                use_external_data=coordinator.should_use_external_data("fundamentals_agent"),
            ))
        if coordinator.is_agent_enabled("macro_agent"):
            data_agents.append(MacroAgent(
                self.settings,
                use_external_data=coordinator.should_use_external_data("macro_agent"),
            ))

        if not data_agents:
            return {}, None

        agent_kwargs = {
            "tickers": tickers,
            "companies": companies,
            "thesis": thesis,
        }
        results, comm_log = await coordinator.coordinate(data_agents, **agent_kwargs)

        # Run Risk Agent on collected findings (round 2)
        news_findings = "No news data available"
        fundamentals_findings = "No fundamentals data available"
        risk_findings = "No risk analysis available"
        macro_findings = "No macro data available"

        if "news_agent" in results:
            news_findings = json.dumps(results["news_agent"].model_dump(), indent=2, default=str)
        if "fundamentals_agent" in results:
            fundamentals_findings = json.dumps(results["fundamentals_agent"].model_dump(), indent=2, default=str)
        if "macro_agent" in results:
            macro_findings = json.dumps(results["macro_agent"].model_dump(), indent=2, default=str)

        if coordinator.is_agent_enabled("risk_agent"):
            risk_agent = RiskAgent(self.settings, use_external_data=False)
            try:
                risk_output = await risk_agent.run(
                    received_messages=coordinator.messages,
                    round_number=2,
                    thesis=thesis,
                )
                results["risk_agent"] = risk_output
                risk_findings = json.dumps(risk_output.model_dump(), indent=2, default=str)
                coordinator.messages.extend(risk_agent.collect_outbox())
            except Exception as e:
                logger.warning(f"Risk agent failed: {e}")

        synthesis_agent = SynthesisAgent(self.settings, use_external_data=False)
        synthesis_output = await synthesis_agent.run(
            thesis=thesis,
            executive_summary=executive_summary,
            risks=risks,
            news_findings=news_findings,
            fundamentals_findings=fundamentals_findings,
            risk_findings=risk_findings,
            macro_findings=macro_findings,
        )

        enrichment = {
            "news_context": results.get("news_agent"),
            "fundamentals_summary": results.get("fundamentals_agent"),
            "macro_context": results.get("macro_agent"),
            "synthesis": synthesis_output,
        }
        return enrichment, comm_log
