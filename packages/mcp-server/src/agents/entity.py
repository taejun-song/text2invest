from models.agent_outputs import EntityOutput
from .base import BaseAgent


class EntityAgent(BaseAgent):
    name = "entity"

    def get_system_prompt(self) -> str:
        return """You are an entity extraction specialist for investment analysis.

Your job is to identify:
1. Company names mentioned in the text
2. Product names or services
3. Macro-economic terms and indicators

Be comprehensive but precise. Only extract entities clearly present in the text.
Do not infer or guess entities not mentioned.

Output valid JSON matching the schema."""

    def get_user_prompt(self, cleaned_text: str, **_kwargs) -> str:
        return f"""Extract all investment-relevant entities from this text:

---
{cleaned_text}
---

Return:
- companies: List of company names
- products: List of product/service names
- macro_terms: List of economic/macro terms (e.g., "inflation", "GDP", "interest rates")"""

    def get_output_model(self) -> type[EntityOutput]:
        return EntityOutput
