from ..agents.base import Agent
from ..core.types import AgentOutput, Action, Message, CopilotInput
from ..core.context import Session
from .copilot import CopilotAgent

class SupportAgent(Agent):
    def __init__(self, notify_human, copilot: CopilotAgent):
        super().__init__("Support")
        self.notify_human = notify_human
        self.copilot = copilot

    async def handle(self, msg: Message, session: Session) -> AgentOutput:
        co = await self.copilot.propose(CopilotInput(message=msg, session=session))
        # envia ao humano do suporte (UI/Slack/etc.)
        self.notify_human(session.user_id, msg.text, co.suggestions)
        return AgentOutput(Action.REPLY, text="Encaminhei para o suporte humano. Um atendente já está vendo.")
