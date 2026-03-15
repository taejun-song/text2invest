from models.collaborative import RiskAgentOutput
from .base import CollaborativeAgent


class RiskAgent(CollaborativeAgent):
    agent_id = "risk_agent"
    name = "Risk Agent"

    def get_tools(self):
        return []

    def get_system_prompt(self) -> str:
        return (
            "You are a risk analysis agent. Your job is to identify and cross-reference risks "
            "from findings provided by other agents (News Agent, Fundamentals Agent, Macro Agent). "
            "You do NOT search for data yourself — you analyze what other agents found.\n\n"
            "Your responsibilities:\n"
            "- Identify risk factors from all agent findings\n"
            "- Track which agent(s) identified each risk (source attribution)\n"
            "- Rank risks by severity\n"
            "- Deduplicate overlapping risks\n"
            "- Flag risks that appear in multiple agent findings as higher priority"
        )

    def get_user_prompt(self, **kwargs) -> str:
        thesis = kwargs.get("thesis", "")
        return (
            f"Investment thesis: {thesis}\n\n"
            f"Review the findings from other agents (provided in the context below) and identify "
            f"all risk factors. For each risk, note which agent(s) identified it. "
            f"Rank risks by severity (most severe first)."
        )

    def get_output_model(self):
        return RiskAgentOutput
