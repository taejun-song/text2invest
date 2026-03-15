import asyncio
import json
import logging
from collections.abc import Callable
from datetime import datetime

from models.idea_report import IdeaReport, UserSettings

ThinkingCallback = Callable[[str, str, str], None]  # agent_id, phase, content
AgentResultCallback = Callable[[str, dict], None]  # agent_id, summary
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
        on_thinking: ThinkingCallback | None = None,
        on_agent_result: AgentResultCallback | None = None,
    ) -> IdeaReport:
        pipeline_start = datetime.now()
        thinking_mode = self.settings.thinking_mode

        def _make_thinking_cb(agent_id: str, phase: str):
            if not on_thinking or not thinking_mode:
                return None
            def cb(content: str):
                on_thinking(agent_id, phase, content)
            return cb

        if on_stage:
            on_stage("extraction")
        extraction_agent = ExtractionAgent(self.settings)
        extraction_output = await extraction_agent.run(
            on_thinking=_make_thinking_cb("extraction_agent", "sequential"),
            text=selection_text,
        )
        if on_agent_result:
            on_agent_result("extraction", {"text_length": len(extraction_output.cleaned_text)})

        if on_stage:
            on_stage("entity")
        entity_agent = EntityAgent(self.settings)
        entity_output = await entity_agent.run(
            on_thinking=_make_thinking_cb("entity_agent", "sequential"),
            cleaned_text=extraction_output.cleaned_text,
        )
        if on_agent_result:
            on_agent_result("entity", {"companies": entity_output.companies[:5]})

        if on_stage:
            on_stage("ticker")
        ticker_agent = TickerAgent(self.settings)
        ticker_output = await ticker_agent.run(
            on_thinking=_make_thinking_cb("ticker_agent", "sequential"),
            companies=entity_output.companies,
        )
        tickers_for_thesis = [t.symbol for t in ticker_output.mappings]
        if on_agent_result:
            on_agent_result("ticker", {"tickers": [{"symbol": t.symbol, "confidence": t.confidence} for t in ticker_output.mappings]})

        if on_stage:
            on_stage("thesis")
        thesis_agent = ThesisAgent(self.settings)
        thesis_output = await thesis_agent.run(
            on_thinking=_make_thinking_cb("thesis_agent", "sequential"),
            cleaned_text=extraction_output.cleaned_text,
            companies=entity_output.companies,
            tickers=tickers_for_thesis,
        )
        if on_agent_result:
            on_agent_result("thesis", {"thesis": thesis_output.thesis[:200], "horizon": thesis_output.horizon.value})

        if on_stage:
            on_stage("critique")
        critique_agent = CritiqueAgent(self.settings)
        critique_output = await critique_agent.run(
            on_thinking=_make_thinking_cb("critique_agent", "sequential"),
            thesis=thesis_output.thesis,
            cleaned_text=extraction_output.cleaned_text,
            companies=entity_output.companies,
        )
        if on_agent_result:
            on_agent_result("critique", {"risks_count": len(critique_output.risks), "risks": critique_output.risks[:3]})

        tickers_for_confidence = [
            {"symbol": t.symbol, "confidence": t.confidence} for t in ticker_output.mappings
        ]

        if on_stage:
            on_stage("confidence")
        confidence_agent = ConfidenceAgent(self.settings)
        confidence_output = await confidence_agent.run(
            on_thinking=_make_thinking_cb("confidence_agent", "sequential"),
            thesis=thesis_output.thesis,
            risks=critique_output.risks,
            counter_thesis=critique_output.counter_thesis,
            missing_info=critique_output.missing_info,
            tickers=tickers_for_confidence,
        )
        if on_agent_result:
            on_agent_result("confidence", {"score": confidence_output.score})

        enrichment = {}
        communication_log = None

        if self._should_run_collaborative():
            try:
                enrichment, communication_log = await self._run_collaborative(
                    tickers=tickers_for_thesis,
                    companies=entity_output.companies,
                    thesis=thesis_output.thesis,
                    executive_summary=[],
                    risks=critique_output.risks,
                    on_stage=on_stage,
                    on_thinking=on_thinking,
                    on_agent_result=on_agent_result,
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
        on_stage: callable = None,
        on_thinking: ThinkingCallback | None = None,
        on_agent_result: AgentResultCallback | None = None,
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

        if on_stage:
            agent_ids = [a.agent_id for a in data_agents]
            on_stage(f"enrichment:{','.join(agent_ids)}")

        agent_kwargs = {
            "tickers": tickers,
            "companies": companies,
            "thesis": thesis,
        }

        def _summarize(agent_id: str, result) -> dict:
            d = result.model_dump()
            if agent_id == "news_agent":
                items = d.get("news_items", [])
                return {"count": len(items), "headlines": [i["headline"][:80] for i in items[:3]], "sentiment": d.get("overall_sentiment", "")}
            if agent_id == "fundamentals_agent":
                snaps = d.get("snapshots", [])
                metrics = snaps[0].get("metrics", [])[:4] if snaps else []
                return {"ticker": snaps[0]["ticker"] if snaps else "", "metrics": [{"name": m["name"], "value": m["value"]} for m in metrics]}
            if agent_id == "macro_agent":
                ctx = d.get("context") or {}
                return {"sector": ctx.get("sector", ""), "headwinds": len(ctx.get("headwinds", [])), "tailwinds": len(ctx.get("tailwinds", []))}
            return {}

        def on_agent_done(agent_id: str):
            if on_stage:
                on_stage(f"agent_done:{agent_id}")
            if on_agent_result and agent_id in results:
                on_agent_result(agent_id, _summarize(agent_id, results[agent_id]))

        results, comm_log = await coordinator.coordinate(
            data_agents, on_agent_done=on_agent_done,
            on_thinking=on_thinking, **agent_kwargs,
        )

        def _compact(obj) -> str:
            return json.dumps(obj.model_dump(), default=str, separators=(",", ":"))[:3000]

        news_findings = _compact(results["news_agent"]) if "news_agent" in results else "N/A"
        fundamentals_findings = _compact(results["fundamentals_agent"]) if "fundamentals_agent" in results else "N/A"
        macro_findings = _compact(results["macro_agent"]) if "macro_agent" in results else "N/A"

        if on_stage:
            on_stage("enrichment:risk_agent,synthesis_agent")

        async def _run_risk():
            if not coordinator.is_agent_enabled("risk_agent"):
                return
            risk_agent = RiskAgent(self.settings, use_external_data=False)
            cb = None
            if on_thinking and self.settings.thinking_mode:
                def cb(content: str):
                    on_thinking("risk_agent", "sequential", content)
            try:
                risk_output = await risk_agent.run(
                    on_thinking=cb,
                    received_messages=coordinator.messages,
                    round_number=2,
                    thesis=thesis,
                )
                results["risk_agent"] = risk_output
                coordinator.messages.extend(risk_agent.collect_outbox())
                if on_stage:
                    on_stage("agent_done:risk_agent")
                if on_agent_result:
                    on_agent_result("risk_agent", {"risks_count": len(risk_output.risks), "top_risk": risk_output.severity_ranking[0] if risk_output.severity_ranking else ""})
            except Exception as e:
                logger.warning(f"Risk agent failed: {e}")

        async def _run_synthesis():
            cb = None
            if on_thinking and self.settings.thinking_mode:
                def cb(content: str):
                    on_thinking("synthesis_agent", "sequential", content)
            agent = SynthesisAgent(self.settings, use_external_data=False)
            return await agent.run(
                on_thinking=cb,
                thesis=thesis,
                executive_summary=executive_summary,
                risks=risks,
                news_findings=news_findings,
                fundamentals_findings=fundamentals_findings,
                risk_findings="N/A",
                macro_findings=macro_findings,
            )

        risk_task = asyncio.ensure_future(_run_risk())
        synthesis_output = await _run_synthesis()
        await risk_task

        enrichment = {
            "news_context": results.get("news_agent"),
            "fundamentals_summary": results.get("fundamentals_agent"),
            "macro_context": results.get("macro_agent"),
            "synthesis": synthesis_output,
        }
        return enrichment, comm_log
