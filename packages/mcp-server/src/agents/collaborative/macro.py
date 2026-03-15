from models.collaborative import MacroAgentOutput
from .base import CollaborativeAgent


class MacroAgent(CollaborativeAgent):
    agent_id = "macro_agent"
    name = "Macro Agent"

    def get_system_prompt(self) -> str:
        return (
            "You are a macro-economic analysis agent. Your job is to analyze sector trends, "
            "economic indicators, and macro-level headwinds and tailwinds relevant to the "
            "companies and investment thesis provided.\n\n"
            "Use web_search to find recent macro-economic data. "
            "If tools are unavailable, use your training knowledge and mark data_source as 'llm_knowledge'.\n\n"
            "Focus on:\n"
            "- Sector identification and positioning\n"
            "- Current sector-level trends\n"
            "- Relevant economic indicators (GDP, interest rates, inflation)\n"
            "- Headwinds (negative macro factors)\n"
            "- Tailwinds (positive macro factors)"
        )

    def get_user_prompt(self, **kwargs) -> str:
        tickers = kwargs.get("tickers", [])
        companies = kwargs.get("companies", [])
        thesis = kwargs.get("thesis", "")
        ticker_str = ", ".join(tickers) if tickers else "none identified"
        company_str = ", ".join(companies) if companies else "none identified"
        return (
            f"Analyze macro-economic context for:\n"
            f"Tickers: {ticker_str}\n"
            f"Companies: {company_str}\n\n"
            f"Investment thesis: {thesis}\n\n"
            f"Identify the relevant sector, current trends, economic indicators, "
            f"and macro-level headwinds/tailwinds that could affect this investment thesis."
        )

    def get_output_model(self):
        return MacroAgentOutput
