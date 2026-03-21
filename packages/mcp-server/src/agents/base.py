import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from models.idea_report import UserSettings
from providers.llm import LLMProvider

ThinkingCallback = Callable[[str], None]

T = TypeVar("T", bound=BaseModel)

LANGUAGE_NAMES = {
    "en": "English", "ko": "Korean", "ja": "Japanese", "zh": "Chinese",
    "es": "Spanish", "fr": "French", "de": "German", "pt": "Portuguese",
    "hi": "Hindi", "ar": "Arabic",
}


class BaseAgent(ABC):
    name: str = "base"
    max_retries: int = 2

    def __init__(self, settings: UserSettings):
        self.settings = settings
        self.llm = LLMProvider(settings)

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def get_user_prompt(self, **kwargs) -> str:
        pass

    @abstractmethod
    def get_output_model(self) -> type[T]:
        pass

    @staticmethod
    def _extract_json(text: str) -> str:
        cleaned = text
        while "<think>" in cleaned:
            s = cleaned.find("<think>")
            e = cleaned.find("</think>")
            cleaned = cleaned[:s] + (cleaned[e + 8:] if e != -1 else "")
        cleaned = cleaned.strip()
        if cleaned.startswith("```"):
            first_nl = cleaned.find("\n")
            if first_nl != -1:
                cleaned = cleaned[first_nl + 1:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        brace = cleaned.find("{")
        if brace == -1:
            return cleaned
        depth, end = 0, brace
        in_str, escape = False, False
        for i in range(brace, len(cleaned)):
            c = cleaned[i]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        return cleaned[brace:end + 1]

    async def run(self, on_thinking: ThinkingCallback | None = None, **kwargs) -> T:
        system_prompt = self.get_system_prompt()
        lang = self.settings.output_language
        if lang and lang != "en" and lang in LANGUAGE_NAMES:
            system_prompt += f"\n\nIMPORTANT: Write all text values in {LANGUAGE_NAMES[lang]}. Keep JSON keys, ticker symbols, numbers, and dates in English."
        user_prompt = self.get_user_prompt(**kwargs)
        output_model = self.get_output_model()
        for attempt in range(self.max_retries):
            try:
                if on_thinking:
                    response = await self.llm.complete_streaming(
                        prompt=user_prompt,
                        system_prompt=system_prompt,
                        response_format=output_model,
                        on_thinking=on_thinking,
                    )
                else:
                    response = await self.llm.complete(
                        prompt=user_prompt,
                        system_prompt=system_prompt,
                        response_format=output_model,
                    )
                data = json.loads(self._extract_json(response))
                return output_model.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt == self.max_retries - 1:
                    raise ValueError(
                        f"Agent {self.name} failed after {self.max_retries} retries: {e}"
                    )
                continue
        raise ValueError(f"Agent {self.name} failed unexpectedly")
