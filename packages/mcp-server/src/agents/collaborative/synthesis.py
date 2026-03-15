from models.collaborative import SynthesisAgentOutput
from .base import CollaborativeAgent


class SynthesisAgent(CollaborativeAgent):
    agent_id = "synthesis_agent"
    name = "Synthesis Agent"

    def get_tools(self):
        return []

    def get_system_prompt(self) -> str:
        return (
            "You are a synthesis agent that combines findings from multiple data agents into a "
            "coherent enriched investment analysis. You integrate news context, financial fundamentals, "
            "and other agent findings with the original text-based thesis.\n\n"
            "Your responsibilities:\n"
            "- Revise the thesis incorporating all agent findings\n"
            "- Create an updated executive summary (max 3 bullets)\n"
            "- Identify convergences (where agents agree)\n"
            "- Identify divergences (where agents disagree)\n"
            "- Deduplicate risks across all sources\n"
            "- Attribute each section to contributing agents"
        )

    def get_user_prompt(self, **kwargs) -> str:
        thesis = kwargs.get("thesis", "")
        executive_summary = kwargs.get("executive_summary", [])
        risks = kwargs.get("risks", [])
        news_findings = kwargs.get("news_findings", "No news data available")
        fundamentals_findings = kwargs.get("fundamentals_findings", "No fundamentals data available")
        risk_findings = kwargs.get("risk_findings", "No risk analysis available")
        macro_findings = kwargs.get("macro_findings", "No macro data available")
        summary_str = "\n".join(f"- {s}" for s in executive_summary) if executive_summary else "None"
        risks_str = "\n".join(f"- {r}" for r in risks) if risks else "None"
        return (
            f"## Original Analysis\n\n"
            f"**Thesis**: {thesis}\n\n"
            f"**Executive Summary**:\n{summary_str}\n\n"
            f"**Risks**:\n{risks_str}\n\n"
            f"## Agent Findings\n\n"
            f"### News Agent:\n{news_findings}\n\n"
            f"### Fundamentals Agent:\n{fundamentals_findings}\n\n"
            f"### Risk Agent:\n{risk_findings}\n\n"
            f"### Macro Agent:\n{macro_findings}\n\n"
            f"Synthesize all findings into a coherent enriched analysis."
        )

    def get_output_model(self):
        return SynthesisAgentOutput
