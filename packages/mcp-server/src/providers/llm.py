import json
import logging
from collections.abc import Callable
from typing import Any

from litellm import acompletion
from pydantic import BaseModel

from models.idea_report import Provider, UserSettings

logger = logging.getLogger(__name__)

ThinkingCallback = Callable[[str], None]


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

    def _build_kwargs(self, thinking_mode: bool | None = None) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self._model_name,
            "temperature": self.settings.temperature,
            "max_tokens": 4096,
            "timeout": 180,
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
            if not thinking_mode:
                kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
                kwargs["temperature"] = max(self.settings.temperature, 0.01)
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

        logger.info(f"LLM call starting: model={kwargs.get('model')}, max_tokens={kwargs.get('max_tokens')}, response_format={kwargs.get('response_format')}")
        response = await acompletion(**kwargs)
        msg = response.choices[0].message
        content = msg.content
        logger.info(f"LLM response: content={'present' if content else 'None'}, len={len(content) if content else 0}, finish={response.choices[0].finish_reason}, tokens={getattr(response, 'usage', None)}")
        if content is None:
            content = getattr(msg, "reasoning", None) or getattr(msg, "reasoning_content", None)
            logger.info(f"Fallback to reasoning: {'found' if content else 'None'}, len={len(content) if content else 0}")
        if content is None:
            raise ValueError("LLM returned empty response")
        cleaned = self._strip_response(content)
        return cleaned if cleaned else content

    @staticmethod
    def _parse_think_tags(text: str) -> tuple[str, str]:
        """Split text into (thinking_content, regular_content) by extracting <think> blocks."""
        thinking_parts: list[str] = []
        content_parts: list[str] = []
        pos = 0
        while pos < len(text):
            start = text.find("<think>", pos)
            if start == -1:
                content_parts.append(text[pos:])
                break
            content_parts.append(text[pos:start])
            end = text.find("</think>", start)
            if end == -1:
                thinking_parts.append(text[start + 7:])
                break
            thinking_parts.append(text[start + 7:end])
            pos = end + 8
        return "".join(thinking_parts), "".join(content_parts)

    async def complete_streaming(
        self,
        prompt: str,
        system_prompt: str | None = None,
        response_format: type[BaseModel] | None = None,
        on_thinking: ThinkingCallback | None = None,
    ) -> str:
        import asyncio
        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        kwargs = self._build_kwargs(thinking_mode=True)
        kwargs["messages"] = messages
        kwargs["stream"] = True
        if response_format:
            kwargs["response_format"] = {"type": "json_object"}
            if system_prompt:
                messages[0]["content"] += (
                    f"\n\nYou MUST respond with valid JSON matching this schema:\n"
                    f"{json.dumps(response_format.model_json_schema(), indent=2)}"
                )
        response = await acompletion(**kwargs)
        buffer = ""
        inside_think = False
        content_parts: list[str] = []
        empty_chunk_count = 0
        stream_iter = response.__aiter__()
        while True:
            try:
                chunk = await asyncio.wait_for(stream_iter.__anext__(), timeout=60)
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError:
                logger.warning("Stream chunk timeout, ending stream")
                break
            delta = chunk.choices[0].delta
            text = delta.content or ""
            if not text:
                empty_chunk_count += 1
                if empty_chunk_count > 100:
                    logger.warning("Too many empty chunks, breaking stream")
                    break
                continue
            empty_chunk_count = 0
            buffer += text
            while True:
                if inside_think:
                    end_idx = buffer.find("</think>")
                    if end_idx == -1:
                        if on_thinking and buffer:
                            on_thinking(buffer)
                        buffer = ""
                        break
                    thinking_chunk = buffer[:end_idx]
                    if on_thinking and thinking_chunk:
                        on_thinking(thinking_chunk)
                    buffer = buffer[end_idx + 8:]
                    inside_think = False
                else:
                    start_idx = buffer.find("<think>")
                    if start_idx == -1:
                        if len(buffer) > 7:
                            safe = buffer[:-7]
                            content_parts.append(safe)
                            buffer = buffer[-7:]
                        break
                    content_parts.append(buffer[:start_idx])
                    buffer = buffer[start_idx + 7:]
                    inside_think = True
        if buffer and not inside_think:
            content_parts.append(buffer)
        elif buffer and inside_think and on_thinking:
            on_thinking(buffer)
        content = "".join(content_parts).strip()
        if not content:
            raise ValueError("LLM returned empty response")
        return content

    @staticmethod
    def _strip_response(text: str) -> str:
        _, cleaned = LLMProvider._parse_think_tags(text)
        cleaned = cleaned.strip()
        if cleaned.startswith("```"):
            first_nl = cleaned.find("\n")
            if first_nl != -1:
                cleaned = cleaned[first_nl + 1:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        return cleaned

    async def complete_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_executor: Any,
        max_iterations: int = 3,
        on_thinking: ThinkingCallback | None = None,
        thinking_mode: bool = False,
    ) -> str:
        kwargs = self._build_kwargs(thinking_mode=thinking_mode)
        kwargs["messages"] = list(messages)
        kwargs["tools"] = tools
        first_call = True
        for _ in range(max_iterations):
            response = await acompletion(**kwargs)
            message = response.choices[0].message
            content = message.content or ""
            if not content:
                content = getattr(message, "reasoning", None) or getattr(message, "reasoning_content", None) or ""
            if first_call and thinking_mode and on_thinking and content:
                thinking, _ = self._parse_think_tags(content)
                if thinking:
                    on_thinking(thinking)
                first_call = False
            if not message.tool_calls:
                cleaned = self._strip_response(content)
                if cleaned:
                    return cleaned
                break
            msg_dump = message.model_dump()
            if first_call:
                first_call = False
            kwargs["messages"].append(msg_dump)
            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                result = await tool_executor(fn_name, fn_args)
                kwargs["messages"].append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result) if not isinstance(result, str) else result,
                })
        kwargs.pop("tools", None)
        kwargs["messages"].append({"role": "user", "content": "Now respond with ONLY valid JSON. No markdown, no explanation."})
        last_response = await acompletion(**kwargs)
        last_msg = last_response.choices[0].message
        last_content = last_msg.content or getattr(last_msg, "reasoning", None) or getattr(last_msg, "reasoning_content", None) or ""
        return self._strip_response(last_content)


async def complete(
    settings: UserSettings,
    prompt: str,
    system_prompt: str | None = None,
    response_format: type[BaseModel] | None = None,
) -> str:
    provider = LLMProvider(settings)
    return await provider.complete(prompt, system_prompt, response_format)
