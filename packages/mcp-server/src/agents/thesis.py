from models.agent_outputs import ThesisOutput
from .base import BaseAgent


class ThesisAgent(BaseAgent):
    name = "thesis"

    def get_system_prompt(self) -> str:
        return """You are an investment thesis generator.

Your job is to create a structured investment thesis GROUNDED STRICTLY in the provided text.

Rules:
1. Your thesis must be directly supported by quotes from the text
2. Do not make claims not supported by the text
3. Identify catalysts (positive triggers) mentioned or implied
4. Determine an appropriate time horizon:
   - "short": Days to weeks
   - "medium": Months to a year
   - "long": Multiple years
5. For each supporting quote, provide exact character offsets

Output valid JSON matching the schema."""

    def get_user_prompt(
        self, cleaned_text: str, companies: list[str], tickers: list[str], **_kwargs
    ) -> str:
        context = f"Companies: {', '.join(companies)}" if companies else "No specific companies"
        ticker_str = f"Tickers: {', '.join(tickers)}" if tickers else "No tickers identified"

        return f"""Generate an investment thesis based on this text:

---
{cleaned_text}
---

{context}
{ticker_str}

Your thesis must:
1. Be grounded in the text (include supporting_quotes with exact quotes and offsets)
2. Identify catalysts mentioned
3. Determine appropriate time horizon

Remember: Only claim what the text supports."""

    def get_output_model(self) -> type[ThesisOutput]:
        return ThesisOutput
