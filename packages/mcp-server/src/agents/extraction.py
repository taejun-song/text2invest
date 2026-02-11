from models.agent_outputs import ExtractionOutput
from .base import BaseAgent


class ExtractionAgent(BaseAgent):
    name = "extraction"

    def get_system_prompt(self) -> str:
        return """You are a text extraction specialist. Your job is to clean and normalize raw text for investment analysis.

You must:
1. Remove excessive whitespace, special characters, and formatting artifacts
2. Preserve the semantic meaning and key financial terms
3. Detect the language of the text
4. Count the words/tokens

Output valid JSON matching the schema."""

    def get_user_prompt(self, text: str, **_kwargs) -> str:
        return f"""Clean and normalize the following text for investment analysis:

---
{text}
---

Return cleaned_text, language code (e.g., "en"), and word_count."""

    def get_output_model(self) -> type[ExtractionOutput]:
        return ExtractionOutput
