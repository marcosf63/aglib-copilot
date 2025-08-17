from ..core.registry import AgentRegistry
from ..core.types import Message, AgentOutput, Action
from ..core.context import Session
from ..policies.handoff import HandoffPolicy


class Router:
    def __init__(self, registry: AgentRegistry, handoff: HandoffPolicy):
        self.registry = registry
        self.handoff = handoff

    async def dispatch(
        self, entry_agent: str, msg: Message, session: Session
    ) -> AgentOutput:
        agent = self.registry.get(entry_agent)
        out = await agent.handle(msg, session)
        session.last_agent = agent.name

        if out.action == Action.HANDOFF and out.target_agent:
            target = self.registry.get(out.target_agent)
            return await target.handle(msg, session)

        if out.action == Action.ESCALATE:
            return await self.registry.get("Support").handle(msg, session)

        if out.action == Action.TO_HUMAN:
            return await self.registry.get("HumanBridge").handle(msg, session)

        if out.action in (Action.REPLY, Action.NOOP):
            return out

        dest = self.handoff.select_specialist(msg)
        if dest and self.registry.has(dest):
            return await self.registry.get(dest).handle(msg, session)

        return await self.registry.get("Support").handle(msg, session)
