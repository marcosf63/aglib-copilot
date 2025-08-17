#!/usr/bin/env python3

"""
Exemplo demonstrando o sistema AgLib com integração LLM e Tools
Este exemplo mostra como os agentes usam LLMs e ferramentas para processamento inteligente
"""

import asyncio
import os
from aglib.core.registry import AgentRegistry
from aglib.core.routing import Router
from aglib.core.types import Message
from aglib.core.context import Session, CustomerProfile
from aglib.policies.handoff import HandoffPolicy
from aglib.agents.pilot import PilotAgent
from aglib.agents.consultant import ConsultantHub, ImageConsultant

# Registrar todas as tools
from aglib.tools.scheduling import register_scheduling_tools
from aglib.tools.payments import register_payment_tools
from aglib.tools.crm import register_crm_tools


# Mock specialist agents (sem LLM por enquanto para este exemplo)
class MockSchedulingSpecialist:
    def __init__(self):
        self.name = "SchedulingSpecialist"

    async def handle(self, msg, session):
        from aglib.core.types import AgentOutput, Action

        return AgentOutput(
            Action.REPLY,
            text="[Mock] Especialista em agendamentos processou sua solicitação. Em breve teremos LLM integrado!",
        )


class MockPaymentsSpecialist:
    def __init__(self):
        self.name = "PaymentsSpecialist"

    async def handle(self, msg, session):
        from aglib.core.types import AgentOutput, Action

        return AgentOutput(
            Action.REPLY,
            text="[Mock] Especialista em pagamentos processou sua solicitação. Em breve teremos LLM integrado!",
        )


class MockSupportAgent:
    def __init__(self):
        self.name = "Support"

    async def handle(self, msg, session):
        from aglib.core.types import AgentOutput, Action

        return AgentOutput(
            Action.REPLY,
            text="[Mock] Agente de suporte processou sua solicitação. Em breve teremos LLM integrado!",
        )


class MockHumanBridge:
    def __init__(self):
        self.name = "HumanBridge"

    async def handle(self, msg, session):
        from aglib.core.types import AgentOutput, Action

        return AgentOutput(
            Action.REPLY, text="[Mock] Conectando com consultor humano..."
        )


async def setup_demo_environment():
    """Setup demo customer data and environment"""
    print("🔧 Configurando ambiente de demonstração...")

    # Registrar todas as tools
    register_scheduling_tools()
    register_payment_tools()
    register_crm_tools()

    # Criar perfil de cliente demo
    session = Session(user_id="demo_user", channel="web")

    # Adicionar perfil de cliente
    customer_profile = CustomerProfile(
        user_id="demo_user",
        name="João Silva",
        email="joao@email.com",
        tier="vip",
        preferences={"preferred_time": "morning"},
    )

    session.business_context.customer_profile = customer_profile

    # Adicionar histórico de pedidos
    session.business_context.order_history = [
        {
            "id": "order1",
            "date": "2025-08-01",
            "total": 45.00,
            "service": "corte_masculino",
        },
        {
            "id": "order2",
            "date": "2025-07-15",
            "total": 70.00,
            "service": "corte_masculino + barba",
        },
    ]

    return session


async def test_llm_integration():
    """Teste principal do sistema com LLM"""
    print("🚀 Iniciando teste do sistema AgLib com LLM...\n")

    # Setup
    session = await setup_demo_environment()

    # Verificar se há chaves de API disponíveis
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))

    if not has_openai and not has_anthropic:
        print("⚠️  AVISO: Nenhuma chave de API LLM encontrada.")
        print("   Para testar completamente, configure:")
        print("   export OPENAI_API_KEY=sua_chave")
        print("   ou")
        print("   export ANTHROPIC_API_KEY=sua_chave")
        print("   O sistema funcionará em modo fallback.\n")

    # Criar agentes
    print("🤖 Criando agentes com configuração LLM...")
    hub = ConsultantHub().add(ImageConsultant())
    pilot = PilotAgent("Pilot", consultants=hub)

    registry = (
        AgentRegistry()
        .add(pilot)
        .add(MockSchedulingSpecialist())
        .add(MockPaymentsSpecialist())
        .add(MockSupportAgent())
        .add(MockHumanBridge())
    )

    router = Router(registry, HandoffPolicy())

    print("   Pilot Agent configurado:")
    print(f"   - LLM: {pilot.config.llm_model}")
    print(f"   - Tools disponíveis: {len(pilot.available_tools)}")
    print(f"   - Pode usar LLM: {pilot.capabilities.can_call_llm}")
    print()

    # Cenários de teste
    test_scenarios = [
        {
            "name": "Saudação Inteligente",
            "message": "Olá! Sou novo aqui",
            "description": "Testa saudação com análise de contexto do cliente",
        },
        {
            "name": "Consulta de Perfil",
            "message": "Quais são minhas informações cadastradas?",
            "description": "Testa uso da tool get_customer_profile",
        },
        {
            "name": "Agendamento com Contexto",
            "message": "Quero agendar um horário para amanhã",
            "description": "Testa roteamento inteligente para especialista",
        },
        {
            "name": "Solicitação de Suporte",
            "message": "Estou com um problema no aplicativo",
            "description": "Testa escalação para suporte",
        },
    ]

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"📋 CENÁRIO {i}: {scenario['name']}")
        print(f"   {scenario['description']}")
        print(f"   Mensagem: \"{scenario['message']}\"")
        print()

        try:
            # Processar mensagem
            message = Message(session.user_id, scenario["message"])
            result = await router.dispatch("Pilot", message, session)

            print(f"   ✅ Resposta: {result.text}")
            print(f"   ⚙️  Ação: {result.action}")

            if hasattr(result, "metadata") and result.metadata:
                if "llm_model" in result.metadata:
                    print(f"   🧠 LLM usado: {result.metadata['llm_model']}")
                if "tools_used" in result.metadata:
                    print(f"   🔧 Tools usadas: {result.metadata['tools_used']}")

            # Mostrar métricas do agente
            metrics = pilot.get_metrics()
            if metrics.total_requests > 0:
                print(
                    f"   📊 Métricas: {metrics.successful_requests}/{metrics.total_requests} sucessos"
                )
                if metrics.llm_usage.total_tokens > 0:
                    print(f"   🎯 Tokens usados: {metrics.llm_usage.total_tokens}")

        except Exception as e:
            print(f"   ❌ Erro: {e}")

        print("-" * 50)
        print()

    # Mostrar resumo final
    print("📈 RESUMO FINAL:")
    final_metrics = pilot.get_metrics()
    print(f"   Total de requisições: {final_metrics.total_requests}")
    print(f"   Sucessos: {final_metrics.successful_requests}")
    print(f"   Falhas: {final_metrics.failed_requests}")
    print(f"   Tempo médio de resposta: {final_metrics.average_response_time:.2f}s")
    print(f"   Tokens LLM utilizados: {final_metrics.llm_usage.total_tokens}")

    if final_metrics.tool_usage_count:
        print("   Tools mais utilizadas:")
        for tool, count in final_metrics.tool_usage_count.items():
            print(f"     - {tool}: {count}x")

    print("\n🎉 Teste concluído!")


async def test_tools_directly():
    """Teste direto das tools para demonstração"""
    print("\n🔧 TESTE DIRETO DAS TOOLS:")
    print("-" * 30)

    # Registrar tools se ainda não foram
    register_crm_tools()

    from aglib.core.tools import tool_registry

    # Teste 1: Get customer profile
    print("1. Buscando perfil do cliente...")
    result = await tool_registry.execute_tool(
        "get_customer_profile", {"user_id": "user123"}
    )
    print(f"   Status: {result.status}")
    if result.status.value == "success" and result.result:
        profile = result.result.get("profile", {})
        print(
            f"   Cliente: {profile.get('name', 'N/A')} ({profile.get('tier', 'regular')})"
        )

    # Teste 2: Create interaction log
    print("\n2. Registrando interação...")
    result = await tool_registry.execute_tool(
        "log_interaction",
        {
            "user_id": "user123",
            "interaction_type": "chat",
            "details": {"message": "Cliente testou o sistema", "satisfaction": "high"},
        },
    )
    print(f"   Status: {result.status}")
    if result.status.value == "success":
        print("   Interação registrada com sucesso!")

    print()


if __name__ == "__main__":

    async def main():
        await test_llm_integration()
        await test_tools_directly()

    # Configurar logging básico
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    asyncio.run(main())
