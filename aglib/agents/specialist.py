from ..agents.base import Agent
from ..core.types import AgentOutput, Action, Message
from ..core.context import Session

class SchedulingSpecialist(Agent):
    def __init__(self):
        super().__init__("Specialist:Scheduling")

    async def handle(self, msg: Message, session: Session) -> AgentOutput:
        return AgentOutput(Action.REPLY, text="Para agendar, informe o serviço e um horário preferido (ex.: amanhã 10h).")

class PaymentsSpecialist(Agent):
    def __init__(self):
        super().__init__("Specialist:Payments")

    async def handle(self, msg: Message, session: Session) -> AgentOutput:
        return AgentOutput(Action.REPLY, text="Para pagamentos: PIX, cartão ou link. Qual prefere?")
