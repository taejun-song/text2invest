import logging
from datetime import datetime
from models.collaborative import (
    DataSource,
    FinancialMetric,
    FundamentalsAgentOutput,
    FundamentalsSnapshot,
)
from providers.fundamentals.service import get_fundamentals_service
from providers.fundamentals.formatters import format_percentage
from .base import CollaborativeAgent

logger = logging.getLogger(__name__)


class FundamentalsAgent(CollaborativeAgent):
    agent_id = "fundamentals_agent"
    name = "Fundamentals Agent"

    def get_system_prompt(self) -> str:
        return (
            "You are a financial fundamentals research agent. Your job is to find key financial metrics "
            "for the companies provided, including revenue, earnings, P/E ratio, market cap, growth rates, "
            "and other relevant financial data.\n\n"
            "Use web_search to find financial data from reliable sources. "
            "If tools are unavailable, use your training knowledge and mark data_source as 'llm_knowledge'.\n\n"
            "Focus on:\n"
            "- Revenue and earnings (most recent quarter/year)\n"
            "- Valuation metrics (P/E, P/S, EV/EBITDA)\n"
            "- Growth rates (revenue growth, EPS growth)\n"
            "- Profitability (margins, ROE)\n"
            "- Balance sheet health (debt/equity, cash position)"
        )

    def get_user_prompt(self, **kwargs) -> str:
        tickers = kwargs.get("tickers", [])
        companies = kwargs.get("companies", [])
        ticker_str = ", ".join(tickers) if tickers else "none identified"
        company_str = ", ".join(companies) if companies else "none identified"
        return (
            f"Retrieve financial fundamentals for:\n"
            f"Tickers: {ticker_str}\n"
            f"Companies: {company_str}\n\n"
            f"For each company, find the most important financial metrics. "
            f"Include the reporting period for each metric when available."
        )

    def get_output_model(self):
        return FundamentalsAgentOutput

    async def run_with_real_data(self, tickers: list[str]) -> FundamentalsAgentOutput:
        service = get_fundamentals_service()
        data = await service.get_fundamentals_batch(tickers)
        snapshots: list[FundamentalsSnapshot] = []
        for ticker, fund_data in data.items():
            if fund_data.data_unavailable:
                continue
            m = fund_data.metrics
            metrics = []
            if m.pe_ratio is not None:
                metrics.append(FinancialMetric(name="P/E Ratio", value=f"{m.pe_ratio:.2f}"))
            if m.market_cap:
                metrics.append(FinancialMetric(name="Market Cap", value=m.market_cap))
            if m.dividend_yield is not None:
                metrics.append(FinancialMetric(name="Dividend Yield", value=format_percentage(m.dividend_yield) or "N/A"))
            if m.eps is not None:
                metrics.append(FinancialMetric(name="EPS", value=f"{m.eps:.2f}"))
            if m.fifty_two_week_high and m.fifty_two_week_low:
                metrics.append(FinancialMetric(name="52-Week Range", value=f"{m.fifty_two_week_low} - {m.fifty_two_week_high}"))
            if m.revenue:
                metrics.append(FinancialMetric(name="Revenue", value=m.revenue))
            if m.profit_margin is not None:
                metrics.append(FinancialMetric(name="Profit Margin", value=format_percentage(m.profit_margin) or "N/A"))
            historical = await service.get_historical(ticker)
            historical_dicts = [{"metric_name": t.metric_name, "data_points": [{"period": p.period, "value": p.value} for p in t.data_points]} for t in historical]
            snapshots.append(FundamentalsSnapshot(
                ticker=ticker,
                company_name=fund_data.company_name,
                exchange=fund_data.exchange,
                currency=fund_data.currency,
                metrics=metrics,
                fundamental_data=fund_data.model_dump(),
                historical_trends=historical_dicts,
                data_source=DataSource.WEB_SEARCH,
                retrieved_at=datetime.now(),
            ))
        assessment = self._generate_assessment(snapshots)
        return FundamentalsAgentOutput(
            snapshots=snapshots,
            assessment=assessment,
            confidence_score=0.85 if snapshots else 0.3,
        )

    def _generate_assessment(self, snapshots: list[FundamentalsSnapshot]) -> str:
        if not snapshots:
            return "No fundamental data available for the requested tickers."
        parts = []
        for s in snapshots:
            pe = next((m.value for m in s.metrics if m.name == "P/E Ratio"), None)
            cap = next((m.value for m in s.metrics if m.name == "Market Cap"), None)
            parts.append(f"{s.ticker} ({s.company_name}): P/E {pe or 'N/A'}, Market Cap {cap or 'N/A'}")
        return "; ".join(parts)
