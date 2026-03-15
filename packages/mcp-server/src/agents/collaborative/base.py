import json
import logging
from abc import abstractmethod
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from models.collaborative import AgentMessage, MessageType
from models.idea_report import UserSettings
from providers.llm import LLMProvider
from tools.web_search import TOOL_DEFINITIONS, execute_tool

ThinkingCallback = Callable[[str], None]

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)

LANGUAGE_NAMES = {
    "en": "English", "ko": "Korean", "ja": "Japanese", "zh": "Chinese",
    "es": "Spanish", "fr": "French", "de": "German", "pt": "Portuguese",
    "hi": "Hindi", "ar": "Arabic",
}


class CollaborativeAgent:
    agent_id: str = "base"
    name: str = "Base Collaborative Agent"
    max_retries: int = 2

    def __init__(self, settings: UserSettings, use_external_data: bool = True):
        self.settings = settings
        self.use_external_data = use_external_data
        self.llm = LLMProvider(settings)
        self._outbox: list[AgentMessage] = []

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def get_user_prompt(self, **kwargs) -> str:
        pass

    @abstractmethod
    def get_output_model(self) -> type[T]:
        pass

    def get_tools(self) -> list[dict[str, Any]]:
        if self.use_external_data:
            return TOOL_DEFINITIONS
        return []

    def send_message(
        self,
        recipient: str,
        message_type: MessageType,
        content: dict,
        round_number: int,
    ) -> AgentMessage:
        msg = AgentMessage(
            id=uuid4(),
            sender=self.agent_id,
            recipient=recipient,
            message_type=message_type,
            content=content,
            timestamp=datetime.now(),
            round_number=round_number,
        )
        self._outbox.append(msg)
        return msg

    def collect_outbox(self) -> list[AgentMessage]:
        messages = list(self._outbox)
        self._outbox.clear()
        return messages

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

    @staticmethod
    def _parse_json(text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        import re
        fixed = re.sub(r"(?<!\\)'", '"', text)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
        import ast
        return ast.literal_eval(text)

    def _build_context_from_messages(self, received_messages: list[AgentMessage]) -> str:
        if not received_messages:
            return ""
        parts = ["\n## Findings from other agents:"]
        for msg in received_messages:
            parts.append(f"\n### From {msg.sender} (Round {msg.round_number}):")
            parts.append(json.dumps(msg.content, indent=2))
        return "\n".join(parts)

    async def run(
        self,
        received_messages: list[AgentMessage] | None = None,
        round_number: int = 1,
        on_thinking: ThinkingCallback | None = None,
        **kwargs,
    ) -> T:
        system_prompt = self.get_system_prompt()
        lang = self.settings.output_language
        if lang and lang != "en" and lang in LANGUAGE_NAMES:
            system_prompt += f"\n\nIMPORTANT: Write all text values in {LANGUAGE_NAMES[lang]}. Keep JSON keys, ticker symbols, numbers, and dates in English."
        user_prompt = self.get_user_prompt(**kwargs)
        if received_messages:
            user_prompt += self._build_context_from_messages(received_messages)
        output_model = self.get_output_model()
        tools = self.get_tools()
        thinking_mode = self.settings.thinking_mode
        for attempt in range(self.max_retries):
            try:
                if tools:
                    messages = []
                    if system_prompt:
                        schema_instruction = (
                            f"\n\nAfter gathering information, respond with valid JSON matching this schema:\n"
                            f"{json.dumps(output_model.model_json_schema(), indent=2)}"
                        )
                        messages.append({"role": "system", "content": system_prompt + schema_instruction})
                    messages.append({"role": "user", "content": user_prompt})
                    response = await self.llm.complete_with_tools(
                        messages=messages,
                        tools=tools,
                        tool_executor=execute_tool,
                        on_thinking=on_thinking,
                        thinking_mode=thinking_mode,
                    )
                else:
                    if on_thinking and thinking_mode:
                        schema_instruction = (
                            f"\n\nYou MUST respond with valid JSON matching this schema:\n"
                            f"{json.dumps(output_model.model_json_schema(), indent=2)}"
                        )
                        response = await self.llm.complete_streaming(
                            prompt=user_prompt,
                            system_prompt=(system_prompt or "") + schema_instruction,
                            on_thinking=on_thinking,
                        )
                    else:
                        schema_instruction = (
                            f"\n\nYou MUST respond with valid JSON matching this schema:\n"
                            f"{json.dumps(output_model.model_json_schema(), indent=2)}"
                        )
                        response = await self.llm.complete(
                            prompt=user_prompt,
                            system_prompt=(system_prompt or "") + schema_instruction,
                        )
                extracted = self._extract_json(response)
                data = self._parse_json(extracted)
                result = output_model.model_validate(data)
                self.send_message(
                    recipient="broadcast",
                    message_type=MessageType.FINDING,
                    content=data,
                    round_number=round_number,
                )
                return result
            except (json.JSONDecodeError, ValidationError, ValueError, SyntaxError) as e:
                logger.warning(f"Agent {self.agent_id} attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Agent {self.agent_id} failed after {self.max_retries} retries: {e}")
                continue
        raise ValueError(f"Agent {self.agent_id} failed unexpectedly")
