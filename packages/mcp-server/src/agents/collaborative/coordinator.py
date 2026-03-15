import asyncio
import logging
from datetime import datetime
from uuid import uuid4

from models.collaborative import AgentConfig, AgentMessage, CommunicationLog
from models.idea_report import UserSettings

from .base import CollaborativeAgent

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 120


class Coordinator:
    def __init__(
        self,
        settings: UserSettings,
        max_rounds: int = 3,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.settings = settings
        self.max_rounds = max_rounds
        self.timeout = timeout
        self.messages: list[AgentMessage] = []
        self._agent_configs = self._parse_agent_configs()

    def _parse_agent_configs(self) -> dict[str, AgentConfig]:
        configs: dict[str, AgentConfig] = {}
        if self.settings.agent_configs:
            for cfg in self.settings.agent_configs:
                if isinstance(cfg, AgentConfig):
                    configs[cfg.agent_id] = cfg
                elif isinstance(cfg, dict):
                    config = AgentConfig(**cfg)
                    configs[config.agent_id] = config
        return configs

    def is_agent_enabled(self, agent_id: str) -> bool:
        cfg = self._agent_configs.get(agent_id)
        if cfg is None:
            return True
        return cfg.enabled

    def should_use_external_data(self, agent_id: str) -> bool:
        if not self.settings.web_lookup:
            return False
        cfg = self._agent_configs.get(agent_id)
        if cfg is None:
            return True
        return cfg.use_external_data

    def get_messages_for_agent(self, agent_id: str) -> list[AgentMessage]:
        msgs = [
            m for m in self.messages
            if m.recipient == "broadcast" or m.recipient == agent_id
        ]
        total_len = sum(len(str(m.content)) for m in msgs)
        if total_len > 50000:
            for m in msgs:
                content_str = str(m.content)
                if len(content_str) > 5000:
                    m.content = {"summary": content_str[:5000] + "... (truncated)"}
        return msgs

    async def run_agents_parallel(
        self,
        agents: list[CollaborativeAgent],
        round_number: int = 1,
        **kwargs,
    ) -> dict[str, object]:
        results: dict[str, object] = {}

        async def run_single(agent: CollaborativeAgent):
            try:
                received = self.get_messages_for_agent(agent.agent_id)
                result = await asyncio.wait_for(
                    agent.run(
                        received_messages=received,
                        round_number=round_number,
                        **kwargs,
                    ),
                    timeout=self.timeout,
                )
                new_messages = agent.collect_outbox()
                self.messages.extend(new_messages)
                results[agent.agent_id] = result
            except asyncio.TimeoutError:
                logger.warning(f"Agent {agent.agent_id} timed out in round {round_number}")
            except Exception as e:
                logger.warning(f"Agent {agent.agent_id} failed in round {round_number}: {e}")

        await asyncio.gather(*(run_single(agent) for agent in agents))
        return results

    async def coordinate(
        self,
        agents: list[CollaborativeAgent],
        **kwargs,
    ) -> tuple[dict[str, object], CommunicationLog]:
        start = datetime.now()
        all_results: dict[str, object] = {}

        enabled_agents = [a for a in agents if self.is_agent_enabled(a.agent_id)]
        if not enabled_agents:
            log = CommunicationLog(
                id=uuid4(), messages=[], total_rounds=0,
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )
            return {}, log

        rounds_run = 0
        for round_num in range(1, self.max_rounds + 1):
            round_results = await self.run_agents_parallel(
                enabled_agents, round_number=round_num, **kwargs,
            )
            all_results.update(round_results)
            rounds_run = round_num

            if round_num == 1:
                break

        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        log = CommunicationLog(
            id=uuid4(),
            messages=list(self.messages),
            total_rounds=rounds_run,
            duration_ms=duration_ms,
        )
        return all_results, log
