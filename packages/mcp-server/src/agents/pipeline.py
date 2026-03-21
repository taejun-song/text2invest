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
from .discovery import DiscoveryAgent
from .entity import EntityAgent
from .extraction import ExtractionAgent
from .formatter import FormatterAgent
from .recommendation import RecommendationAgent
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
        logger.info("Pipeline started")

        def _make_thinking_cb(agent_id: str, phase: str):
            if not on_thinking or not thinking_mode:
                return None
            def cb(content: str):
                on_thinking(agent_id, phase, content)
            return cb

        def _make_retry_cb(stage_name: str):
            if not on_stage:
                return None
            def cb(attempt: int, max_retries: int):
                on_stage(f"retry:{stage_name}:{attempt}:{max_retries}")
            return cb

        if on_stage:
            on_stage("extraction")
        extraction_agent = ExtractionAgent(self.settings)
        extraction_output = await extraction_agent.run(
            on_thinking=_make_thinking_cb("extraction_agent", "sequential"),
            on_retry=_make_retry_cb("extraction"),
            text=selection_text,
        )
        logger.info("Extraction done")
        if self.settings.output_language in (None, "", "auto", "en"):
            self.settings.output_language = extraction_output.language
            logger.info(f"Auto-detected output language: {extraction_output.language}")
        if on_agent_result:
            on_agent_result("extraction", {"text_length": len(extraction_output.cleaned_text), "language": extraction_output.language})

        if on_stage:
            on_stage("entity")
        entity_agent = EntityAgent(self.settings)
        entity_output = await entity_agent.run(
            on_thinking=_make_thinking_cb("entity_agent", "sequential"),
            on_retry=_make_retry_cb("entity"),
            cleaned_text=extraction_output.cleaned_text,
        )
        logger.info("Entity done")
        if on_agent_result:
            on_agent_result("entity", {"companies": entity_output.companies[:5]})

        if on_stage:
            on_stage("ticker")
        ticker_agent = TickerAgent(self.settings)
        ticker_output = await ticker_agent.run(
            on_thinking=_make_thinking_cb("ticker_agent", "sequential"),
            on_retry=_make_retry_cb("ticker"),
            companies=entity_output.companies,
            cleaned_text=extraction_output.cleaned_text,
        )
        logger.info("Ticker done")
        tickers_for_thesis = [t.symbol for t in ticker_output.mappings]
        inferred_symbols = [t.symbol for t in ticker_output.inferred_tickers]
        if on_agent_result:
            on_agent_result("ticker", {
                "tickers": [{"symbol": t.symbol, "confidence": t.confidence} for t in ticker_output.mappings],
                "inferred_count": len(ticker_output.inferred_tickers),
                "sectors": [s.name for s in ticker_output.sectors],
            })

        if on_stage:
            on_stage("thesis")
        thesis_agent = ThesisAgent(self.settings)
        thesis_output = await thesis_agent.run(
            on_thinking=_make_thinking_cb("thesis_agent", "sequential"),
            on_retry=_make_retry_cb("thesis"),
            cleaned_text=extraction_output.cleaned_text,
            companies=entity_output.companies,
            tickers=tickers_for_thesis,
        )
        logger.info("Thesis done")
        if on_agent_result:
            on_agent_result("thesis", {
                "thesis": thesis_output.thesis[:300],
                "horizon": thesis_output.horizon.value,
                "catalysts": thesis_output.catalysts[:3],
                "quotes_count": len(thesis_output.supporting_quotes),
            })

        if on_stage:
            on_stage("critique")
        critique_agent = CritiqueAgent(self.settings)
        critique_output = await critique_agent.run(
            on_thinking=_make_thinking_cb("critique_agent", "sequential"),
            on_retry=_make_retry_cb("critique"),
            thesis=thesis_output.thesis,
            cleaned_text=extraction_output.cleaned_text,
            companies=entity_output.companies,
        )
        logger.info("Critique done")
        if on_agent_result:
            on_agent_result("critique", {
                "risks_count": len(critique_output.risks),
                "risks": critique_output.risks[:3],
                "counter_thesis": critique_output.counter_thesis[:200] if critique_output.counter_thesis else "",
            })

        tickers_for_confidence = [
            {"symbol": t.symbol, "confidence": t.confidence} for t in ticker_output.mappings
        ]

        if on_stage:
            on_stage("confidence")
        confidence_agent = ConfidenceAgent(self.settings)
        confidence_output = await confidence_agent.run(
            on_thinking=_make_thinking_cb("confidence_agent", "sequential"),
            on_retry=_make_retry_cb("confidence"),
            thesis=thesis_output.thesis,
            risks=critique_output.risks,
            counter_thesis=critique_output.counter_thesis,
            missing_info=critique_output.missing_info,
            tickers=tickers_for_confidence,
        )
        logger.info("Confidence done")
        if on_agent_result:
            on_agent_result("confidence", {
                "score": confidence_output.score,
                "explanation": confidence_output.explanation[:200] if confidence_output.explanation else "",
            })

        search_depth = self.settings.search_depth.value if hasattr(self.settings.search_depth, 'value') else self.settings.search_depth

        discovered_companies = []
        if search_depth != "focused" and tickers_for_confidence:
            if on_stage:
                on_stage("discovery")
            discovery_agent = DiscoveryAgent(self.settings)
            discovery_output = await discovery_agent.run(
                on_thinking=_make_thinking_cb("discovery_agent", "sequential"),
                on_retry=_make_retry_cb("discovery"),
                tickers=tickers_for_confidence,
                search_depth=search_depth,
            )
            discovered_companies = discovery_output.related_companies
            logger.info(f"Discovery done, found {len(discovered_companies)} related companies")
            if on_agent_result:
                on_agent_result("discovery", {
                    "related_count": len(discovered_companies),
                    "companies": [{"symbol": c.symbol, "name": c.company_name, "relationship": c.relationship.value if hasattr(c.relationship, 'value') else c.relationship} for c in discovered_companies[:5]],
                })

        all_ticker_symbols = tickers_for_thesis + [c.symbol for c in discovered_companies]

        enrichment = {}
        communication_log = None

        if self._should_run_collaborative():
            try:
                enrichment, communication_log = await self._run_collaborative(
                    tickers=all_ticker_symbols,
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
            else:
                logger.info("Collaborative enrichment done")

        enrichment_summary = self._build_enrichment_summary(enrichment)
        related_for_rec = [
            {
                "symbol": c.symbol,
                "company_name": c.company_name,
                "relationship": c.relationship.value if hasattr(c.relationship, 'value') else c.relationship,
                "primary_symbol": c.primary_symbol,
            }
            for c in discovered_companies
        ]

        if on_stage:
            on_stage("recommendation")
        rec_agent = RecommendationAgent(self.settings)
        rec_output = await rec_agent.run(
            on_thinking=_make_thinking_cb("recommendation_agent", "sequential"),
            on_retry=_make_retry_cb("recommendation"),
            tickers=tickers_for_confidence,
            thesis=thesis_output.thesis,
            risks=critique_output.risks,
            catalysts=thesis_output.catalysts,
            confidence_score=confidence_output.score,
            counter_thesis=critique_output.counter_thesis,
            enrichment_summary=enrichment_summary,
            related_tickers=related_for_rec if related_for_rec else None,
        )
        rec_map = {r.symbol: r for r in rec_output.recommendations}
        logger.info("Recommendation done")
        if on_agent_result:
            on_agent_result("recommendation", {
                "count": len(rec_output.recommendations),
                "signals": [{"symbol": r.symbol, "signal": r.signal, "certainty": r.certainty} for r in rec_output.recommendations[:5]],
            })

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
            recommendations=rec_map,
            discovered_companies=discovered_companies,
            search_depth=search_depth,
            sectors=ticker_output.sectors,
            inferred_tickers=ticker_output.inferred_tickers,
        )

    @staticmethod
    def _build_enrichment_summary(enrichment: dict) -> str | None:
        if not enrichment:
            return None
        parts = []
        news = enrichment.get("news_context")
        if news and hasattr(news, "news_items"):
            headlines = [item.headline for item in news.news_items[:5]]
            sentiment = getattr(news, "overall_sentiment", "unknown")
            parts.append(f"News ({sentiment}): " + "; ".join(headlines))
        fund = enrichment.get("fundamentals_summary")
        if fund and hasattr(fund, "snapshots"):
            for snap in fund.snapshots[:3]:
                metrics = ", ".join(f"{m.name}: {m.value}" for m in snap.metrics[:3])
                parts.append(f"Fundamentals [{snap.ticker}]: {metrics}")
        macro = enrichment.get("macro_context")
        if macro and hasattr(macro, "context") and macro.context:
            ctx = macro.context
            parts.append(f"Macro [{ctx.sector}]: headwinds={ctx.headwinds}, tailwinds={ctx.tailwinds}")
        return "\n".join(parts) if parts else None

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

        results: dict = {}

        def on_agent_done(agent_id: str, result: object = None):
            if result is not None:
                results[agent_id] = result
            if on_stage:
                on_stage(f"agent_done:{agent_id}")
            if on_agent_result and agent_id in results:
                on_agent_result(agent_id, _summarize(agent_id, results[agent_id]))

        coord_results, comm_log = await coordinator.coordinate(
            data_agents, on_agent_done=on_agent_done,
            on_thinking=on_thinking, **agent_kwargs,
        )
        results.update(coord_results)

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
