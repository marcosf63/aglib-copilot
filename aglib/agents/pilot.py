from typing import Optional
from ..agents.base import Agent
from ..core.types import AgentOutput, Action, Message, AgentConfig, AgentCapabilities
from ..core.context import Session
from .consultant import ConsultantHub


class PilotAgent(Agent):
    def __init__(
        self, name: Optional[str] = None, consultants: Optional[ConsultantHub] = None
    ):
        # Configure agent for LLM and tools
        config = AgentConfig(
            name=name or "Pilot",
            llm_provider="openai",
            llm_model="gpt-4",
            temperature=0.3,
            max_tokens=2000,
            available_tools=["get_customer_profile", "log_interaction"],
            prompt_template="pilot",
        )

        capabilities = AgentCapabilities(
            can_use_tools=True,
            can_call_llm=True,
            can_escalate=True,
            can_handoff=True,
            allowed_tool_categories=["crm", "general"],
        )

        super().__init__(name or "Pilot", config, capabilities)
        self.consultants = consultants or ConsultantHub()

    async def _handle_without_llm(self, msg: Message, session: Session) -> AgentOutput:
        """Fallback handler when LLM is not available"""
        t = msg.text.lower()

        # saudação
        if any(
            x in t for x in ["oi", "olá", "ola", "bom dia", "boa tarde", "boa noite"]
        ):
            return AgentOutput(
                Action.REPLY,
                text="Oi! Posso ajudar com agendamentos, pagamentos ou até gerar uma imagem. O que você precisa?",
            )

        # delegação para consultor (ex.: gerar imagem) — comunicação *só* Pilot <-> Consultant
        if any(
            x in t
            for x in ["gerar imagem", "criar imagem", "imagem de", "gera uma imagem"]
        ):
            if self.consultants.has("Consultant:Image"):
                # Pilot conversa com o consultor e formata a resposta final
                result = await self.consultants.get("Consultant:Image").handle(
                    msg, session
                )
                img_url = result.payload.get("image_url")
                return AgentOutput(
                    Action.REPLY, text=f"Pronto! Gerei uma imagem para você: {img_url}"
                )
            else:
                return AgentOutput(
                    Action.REPLY,
                    text="Ainda não tenho um consultor de imagens configurado.",
                )

        # pedido explícito por humano => escalar
        if "humano" in t or "atendente" in t or "pessoa" in t:
            return AgentOutput(
                Action.ESCALATE, text="Vou te encaminhar para o suporte humano."
            )

        # caso geral: deixar policy decidir o especialista
        return AgentOutput(
            Action.HANDOFF, text="Entendido. Vou te encaminhar para o melhor agente."
        )
