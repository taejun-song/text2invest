from models.agent_outputs import CritiqueOutput
from .base import BaseAgent


class CritiqueAgent(BaseAgent):
    name = "critique"

    def get_system_prompt(self) -> str:
        return """You are an investment thesis critic and risk analyst.

Your job is to critically evaluate an investment thesis and identify:
1. Risks and potential downsides
2. A counter-thesis (the bear case)
3. Missing information that would strengthen or weaken the thesis

Rules:
1. Be thorough but fair
2. Focus on material risks, not trivial concerns
3. Consider market, company-specific, and macro risks
4. The counter-thesis should be a plausible alternative view
5. Missing info should highlight gaps in the analysis

Output valid JSON matching the schema."""

    def get_user_prompt(
        self, thesis: str, cleaned_text: str, companies: list[str], **_kwargs
    ) -> str:
        context = f"Companies: {', '.join(companies)}" if companies else "No specific companies"

        return f"""Critique this investment thesis:

THESIS:
{thesis}

ORIGINAL TEXT:
{cleaned_text}

{context}

Provide:
1. risks: Material risk factors
2. counter_thesis: The opposing investment view
3. missing_info: What information is missing that would help evaluate this thesis"""

    def get_output_model(self) -> type[CritiqueOutput]:
        return CritiqueOutput
