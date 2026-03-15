import json
from typing import Any

from litellm import acompletion
from pydantic import BaseModel

from models.idea_report import Provider, UserSettings


class LLMProvider:
    def __init__(self, settings: UserSettings):
        self.settings = settings
        self._model_name = self._build_model_name()

    def _build_model_name(self) -> str:
        if self.settings.provider == Provider.OPENAI:
            if self.settings.base_url:
                return f"openai/{self.settings.model}"
            return self.settings.model
        elif self.settings.provider == Provider.ANTHROPIC:
            return f"anthropic/{self.settings.model}"
        elif self.settings.provider == Provider.OLLAMA:
            return f"ollama/{self.settings.model}"
        elif self.settings.provider == Provider.NRP:
            return f"openai/{self.settings.model}"
        else:
            raise ValueError(f"Unknown provider: {self.settings.provider}")

    def _build_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self._model_name,
            "temperature": self.settings.temperature,
        }
        if self.settings.provider == Provider.OPENAI:
            if self.settings.api_key:
                kwargs["api_key"] = self.settings.api_key
            elif self.settings.base_url:
                kwargs["api_key"] = "not-needed"
            if self.settings.base_url:
                kwargs["api_base"] = self.settings.base_url
        elif self.settings.provider == Provider.ANTHROPIC and self.settings.api_key:
            kwargs["api_key"] = self.settings.api_key
        elif self.settings.provider == Provider.OLLAMA and self.settings.base_url:
            kwargs["api_base"] = self.settings.base_url
        elif self.settings.provider == Provider.NRP:
            kwargs["api_key"] = self.settings.api_key
            kwargs["api_base"] = self.settings.base_url or "https://ellm.nrp-nautilus.io/v1"
        return kwargs

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        response_format: type[BaseModel] | None = None,
    ) -> str:
        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs = self._build_kwargs()
        kwargs["messages"] = messages

        if response_format:
            kwargs["response_format"] = {"type": "json_object"}
            if system_prompt:
                messages[0]["content"] += (
                    f"\n\nYou MUST respond with valid JSON matching this schema:\n"
                    f"{json.dumps(response_format.model_json_schema(), indent=2)}"
                )

        response = await acompletion(**kwargs)
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("LLM returned empty response")
        return content

    async def complete_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_executor: Any,
        max_iterations: int = 5,
    ) -> str:
        kwargs = self._build_kwargs()
        kwargs["messages"] = list(messages)
        kwargs["tools"] = tools

        for _ in range(max_iterations):
            response = await acompletion(**kwargs)
            message = response.choices[0].message

            if not message.tool_calls:
                return message.content or ""

            kwargs["messages"].append(message.model_dump())

            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                result = await tool_executor(fn_name, fn_args)
                kwargs["messages"].append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result) if not isinstance(result, str) else result,
                })

        last_response = await acompletion(**{k: v for k, v in kwargs.items() if k != "tools"})
        return last_response.choices[0].message.content or ""


async def complete(
    settings: UserSettings,
    prompt: str,
    system_prompt: str | None = None,
    response_format: type[BaseModel] | None = None,
) -> str:
    provider = LLMProvider(settings)
    return await provider.complete(prompt, system_prompt, response_format)
