from ..models.agent_outputs import TickerOutput
from .base import BaseAgent


class TickerAgent(BaseAgent):
    name = "ticker"

    def get_system_prompt(self) -> str:
        return """You are a stock ticker mapping specialist.

Your job is to map company names to their stock ticker symbols.

Rules:
1. Only map companies you are confident about
2. Use US stock exchanges (NYSE, NASDAQ) when possible
3. If a company is private or you're unsure, do not include it
4. Provide confidence scores:
   - 0.9-1.0: Well-known public company with clear ticker
   - 0.7-0.9: Likely correct but some ambiguity
   - 0.5-0.7: Uncertain, multiple possibilities
   - Below 0.5: Do not include
5. Explain your reasoning for each mapping

Output valid JSON matching the schema."""

    def get_user_prompt(self, companies: list[str], **_kwargs) -> str:
        if not companies:
            return "No companies to map. Return empty mappings list."

        companies_str = "\n".join(f"- {c}" for c in companies)
        return f"""Map these companies to their stock ticker symbols:

{companies_str}

For each company, provide:
- company: The original company name
- symbol: The ticker symbol (uppercase, 1-5 chars)
- confidence: Your confidence (0.0-1.0)
- reasoning: Why you chose this ticker"""

    def get_output_model(self) -> type[TickerOutput]:
        return TickerOutput
