from models.collaborative import NewsAgentOutput
from .base import CollaborativeAgent


class NewsAgent(CollaborativeAgent):
    agent_id = "news_agent"
    name = "News Agent"

    def get_system_prompt(self) -> str:
        return (
            "You are a financial news research agent. Your job is to find and analyze recent news "
            "articles related to the companies and topics provided. For each news item, assess its "
            "sentiment (positive/negative/neutral) and relevance to the investment thesis.\n\n"
            "Use the news_search and web_search tools to find recent articles. "
            "If tools are unavailable, use your training knowledge and mark data_source as 'llm_knowledge'.\n\n"
            "Focus on:\n"
            "- Recent earnings reports and financial results\n"
            "- Product launches and strategic announcements\n"
            "- Regulatory changes affecting the company\n"
            "- Market sentiment and analyst opinions\n"
            "- Competitive developments"
        )

    def get_user_prompt(self, **kwargs) -> str:
        tickers = kwargs.get("tickers", [])
        companies = kwargs.get("companies", [])
        thesis = kwargs.get("thesis", "")
        ticker_str = ", ".join(tickers) if tickers else "none identified"
        company_str = ", ".join(companies) if companies else "none identified"
        return (
            f"Find recent news about these companies/tickers:\n"
            f"Tickers: {ticker_str}\n"
            f"Companies: {company_str}\n\n"
            f"Investment thesis context: {thesis}\n\n"
            f"Search for relevant news articles and analyze their sentiment and relevance to the thesis. "
            f"Return up to 5 most relevant news items."
        )

    def get_output_model(self):
        return NewsAgentOutput
