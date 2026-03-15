import json
import logging
from abc import abstractmethod
from datetime import datetime
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from models.collaborative import AgentMessage, MessageType
from models.idea_report import UserSettings
from providers.llm import LLMProvider
from tools.web_search import TOOL_DEFINITIONS, execute_tool

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class CollaborativeAgent:
    agent_id: str = "base"
    name: str = "Base Collaborative Agent"
    max_retries: int = 3

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
        **kwargs,
    ) -> T:
        system_prompt = self.get_system_prompt()
        user_prompt = self.get_user_prompt(**kwargs)

        if received_messages:
            user_prompt += self._build_context_from_messages(received_messages)

        output_model = self.get_output_model()
        tools = self.get_tools()

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

                data = json.loads(response)
                result = output_model.model_validate(data)

                self.send_message(
                    recipient="broadcast",
                    message_type=MessageType.FINDING,
                    content=data,
                    round_number=round_number,
                )
                return result
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Agent {self.agent_id} attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Agent {self.agent_id} failed after {self.max_retries} retries: {e}")
                continue
        raise ValueError(f"Agent {self.agent_id} failed unexpectedly")
