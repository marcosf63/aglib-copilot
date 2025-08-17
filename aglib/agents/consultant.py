from typing import Dict, Optional
from ..agents.base import Agent
from ..core.types import AgentOutput, Action, Message
from ..core.context import Session

class ConsultantHub:
    """Registro simples de consultores; usado *somente* pelo Pilot."""
    def __init__(self):
        self._items: Dict[str, Agent] = {}

    def add(self, agent: Agent) -> "ConsultantHub":
        self._items[agent.name] = agent
        return self

    def get(self, name: str) -> Agent:
        return self._items[name]

    def has(self, name: str) -> bool:
        return name in self._items


class ImageConsultant(Agent):
    """Exemplo de consultor: gera imagem (stub)."""
    def __init__(self):
        super().__init__("Consultant:Image")

    async def _handle_without_llm(self, msg: Message, session: Session) -> AgentOutput:
        # Aqui você pluga a geração real (Stable Diffusion / DALL·E / etc.)
        prompt = msg.text
        url = f"https://example.com/fake_image?prompt={prompt.replace(' ', '+')}"
        return AgentOutput(
            action=Action.NOOP,
            text=f"[consultor] imagem gerada (stub): {url}",
            payload={"image_url": url, "prompt": prompt}
        )
