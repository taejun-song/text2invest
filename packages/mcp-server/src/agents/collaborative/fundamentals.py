from models.collaborative import FundamentalsAgentOutput
from .base import CollaborativeAgent


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
