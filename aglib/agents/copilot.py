from typing import List
from ..core.types import CopilotInput, CopilotOutput, Suggestion


class CopilotTools:
    async def fetch_crm(self, user_id: str) -> dict:
        return {}

    async def search_kb(self, query: str) -> List[str]:
        return []

    async def create_ticket(self, payload: dict) -> str:
        return "TCK-0001"


class CopilotAgent:
    def __init__(self, tools: CopilotTools):
        self.tools = tools
        self.name = "Copilot"

    async def propose(self, ci: CopilotInput) -> CopilotOutput:
        t = ci.message.text.lower()
        kb = await self.tools.search_kb(t) if len(t) > 6 else []
        crm = await self.tools.fetch_crm(ci.session.user_id)

        draft = "Rascunho de resposta: "
        if "agendar" in t:
            draft += "Podemos oferecer horários amanhã às 10h ou 14h. Qual prefere?"
        elif "pagamento" in t or "pagar" in t:
            draft += "Posso emitir link de pagamento ou PIX. Tem preferência?"
        else:
            draft += "Obrigado pelo contato! Já estou analisando seu caso."

        if kb:
            draft += "\n\nNotas da KB:\n- " + "\n- ".join(kb[:3])
        if crm:
            draft += f"\n\nContexto CRM: {crm.get('status','sem status')}"

        s1 = Suggestion(text=draft, confidence=0.72)
        s2 = Suggestion(
            text="Confirmo dados e abro ticket prioritário.",
            confidence=0.55,
            actions={"create_ticket": {"priority": "high"}},
        )
        return CopilotOutput(suggestions=[s1, s2])
