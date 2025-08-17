import asyncio
from aglib.core.registry import AgentRegistry
from aglib.core.routing import Router
from aglib.core.types import Message
from aglib.core.context import Session
from aglib.policies.handoff import HandoffPolicy
from aglib.agents.pilot import PilotAgent
from aglib.agents.specialist import SchedulingSpecialist, PaymentsSpecialist
from aglib.agents.support import SupportAgent
from aglib.agents.human_bridge import HumanBridge
from aglib.agents.copilot import CopilotAgent, CopilotTools
from aglib.agents.consultant import ConsultantHub, ImageConsultant


class DemoTools(CopilotTools):
    async def fetch_crm(self, user_id: str) -> dict:
        return {"status": "cliente VIP", "last_order": "2025-08-05"}

    async def search_kb(self, query: str):
        return ["Procedimento X passo-a-passo", "SLA: 24h", "Escalada N2 se falhar"]


def notify_support_human(user_id: str, text: str, suggestions):
    print(f"[SUPORTE HUMANO] de {user_id}: {text}")
    for i, s in enumerate(suggestions, 1):
        print(
            f"  Sugestão {i} (conf {s.confidence:.2f}):\n{s.text}\nAções: {s.actions}\n"
        )


def notify_consultant(user_id: str, text: str):
    print(f"[CONSULTOR HUMANO] de {user_id}: {text}")


async def main():
    # monta hub de consultores e injeta no Pilot
    hub = ConsultantHub().add(ImageConsultant())
    pilot = PilotAgent("Pilot", consultants=hub)

    copilot = CopilotAgent(DemoTools())
    reg = (
        AgentRegistry()
        .add(pilot)
        .add(SchedulingSpecialist())
        .add(PaymentsSpecialist())
        .add(SupportAgent(notify_support_human, copilot))
        .add(HumanBridge(notify_consultant))
    )

    router = Router(reg, HandoffPolicy())
    session = Session(user_id="u123", channel="web")

    print("--- CENÁRIO 1: saudação ---")
    out = await router.dispatch("Pilot", Message("u123", "Olá!"), session)
    print("BOT:", out.text)

    print("\n--- CENÁRIO 2: gerar imagem via Consultor ---")
    out = await router.dispatch(
        "Pilot",
        Message("u123", "Quero gerar imagem de um corte de cabelo moderno"),
        session,
    )
    print("BOT:", out.text)

    print("\n--- CENÁRIO 3: intenção de agendar (vai p/ especialista) ---")
    out = await router.dispatch(
        "Pilot", Message("u123", "Quero agendar amanhã"), session
    )
    print("BOT:", out.text)

    print("\n--- CENÁRIO 4: pedir humano (escala p/ suporte) ---")
    out = await router.dispatch(
        "Pilot", Message("u123", "Quero falar com um atendente humano"), session
    )
    print("BOT:", out.text)


if __name__ == "__main__":
    asyncio.run(main())
