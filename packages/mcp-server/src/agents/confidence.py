from models.agent_outputs import ConfidenceOutput
from .base import BaseAgent


class ConfidenceAgent(BaseAgent):
    name = "confidence"

    def get_system_prompt(self) -> str:
        return """You are a confidence calibration specialist for investment theses.

Your job is to assign a well-calibrated confidence score to an investment thesis.

Calibration guidelines:
- 0.8-1.0: Strong thesis with clear evidence, identified company, and actionable catalysts
- 0.6-0.8: Reasonable thesis with some uncertainty or missing information
- 0.4-0.6: Speculative thesis with significant gaps or ambiguity
- 0.2-0.4: Weak thesis with little supporting evidence
- 0.0-0.2: Very weak or contradictory thesis

Consider:
1. Quality and specificity of source text
2. Clarity of company/ticker identification
3. Strength of supporting evidence
4. Presence of clear catalysts
5. Time horizon appropriateness
6. Identified risks and counter-thesis strength

Output valid JSON matching the schema."""

    def get_user_prompt(
        self,
        thesis: str,
        risks: list[str],
        counter_thesis: str,
        missing_info: list[str],
        tickers: list[dict],
        **_kwargs,
    ) -> str:
        ticker_str = (
            ", ".join(f"{t['symbol']} ({t['confidence']:.2f})" for t in tickers)
            if tickers
            else "None identified"
        )
        risks_str = "\n".join(f"- {r}" for r in risks) if risks else "None identified"
        missing_str = "\n".join(f"- {m}" for m in missing_info) if missing_info else "None"

        return f"""Calibrate confidence for this investment thesis:

THESIS:
{thesis}

TICKERS: {ticker_str}

RISKS:
{risks_str}

COUNTER-THESIS:
{counter_thesis}

MISSING INFORMATION:
{missing_str}

Provide:
1. score: Your calibrated confidence (0.0-1.0)
2. explanation: Why this confidence level
3. limitations: Known weaknesses in the analysis"""

    def get_output_model(self) -> type[ConfidenceOutput]:
        return ConfidenceOutput
