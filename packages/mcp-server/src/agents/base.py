import json
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ..models.idea_report import UserSettings
from ..providers.llm import LLMProvider

T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC):
    name: str = "base"
    max_retries: int = 3

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

    async def run(self, **kwargs) -> T:
        system_prompt = self.get_system_prompt()
        user_prompt = self.get_user_prompt(**kwargs)
        output_model = self.get_output_model()

        for attempt in range(self.max_retries):
            try:
                response = await self.llm.complete(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    response_format=output_model,
                )
                data = json.loads(response)
                return output_model.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt == self.max_retries - 1:
                    raise ValueError(
                        f"Agent {self.name} failed after {self.max_retries} retries: {e}"
                    )
                continue
        raise ValueError(f"Agent {self.name} failed unexpectedly")
