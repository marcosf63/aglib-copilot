from typing import Dict
from .types import Message
from ..agents.base import Agent

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Agent] = {}

    def add(self, agent: Agent) -> "AgentRegistry":
        self._agents[agent.name] = agent
        return self

    def get(self, name: str) -> Agent:
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' não registrado")
        return self._agents[name]

    def has(self, name: str) -> bool:
        return name in self._agents
