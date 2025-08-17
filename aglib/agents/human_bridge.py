from ..agents.base import Agent
from ..core.types import AgentOutput, Action, Message
from ..core.context import Session


class HumanBridge(Agent):
    def __init__(self, send_to_consultant):
        super().__init__("HumanBridge")
        self.send_to_consultant = send_to_consultant

    async def handle(self, msg: Message, session: Session) -> AgentOutput:
        self.send_to_consultant(session.user_id, msg.text)
        return AgentOutput(
            Action.REPLY, text="Conectei você a um consultor humano. Aguarde por favor."
        )
