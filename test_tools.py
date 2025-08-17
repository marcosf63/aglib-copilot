#!/usr/bin/env python3

"""
Teste simples para verificar se o sistema de tools está funcionando
"""

import asyncio
from aglib.core.tools import tool_registry
from aglib.tools.scheduling import register_scheduling_tools
from aglib.tools.payments import register_payment_tools


async def test_tools():
    print("=== Teste do Sistema de Tools ===\n")
    
    # Registrar tools
    print("1. Registrando tools...")
    register_scheduling_tools()
    register_payment_tools()
    
    print(f"   Tools registradas: {len(tool_registry.list_tool_names())}")
    print(f"   Categorias: {tool_registry.list_categories()}")
    print()
    
    # Teste 1: Verificar disponibilidade
    print("2. Testando CheckAvailabilityTool...")
    result = await tool_registry.execute_tool(
        "check_availability",
        {"date": "2025-08-18", "service": "corte_masculino"}
    )
    print(f"   Status: {result.status}")
    if result.status.value == "success":
        print(f"   Horários disponíveis: {len(result.result['available_slots'])}")
    else:
        print(f"   Erro: {result.error_message}")
    print()
    
    # Teste 2: Fazer um agendamento
    print("3. Testando BookAppointmentTool...")
    result = await tool_registry.execute_tool(
        "book_appointment",
        {
            "user_id": "user123",
            "date": "2025-08-18",
            "time": "10:00",
            "service": "corte_masculino",
            "notes": "Teste de agendamento"
        }
    )
    print(f"   Status: {result.status}")
    if result.status.value == "success":
        print(f"   Agendamento ID: {result.result['appointment']['id']}")
    else:
        print(f"   Erro: {result.error_message}")
    print()
    
    # Teste 3: Listar métodos de pagamento
    print("4. Testando GetPaymentMethodsTool...")
    result = await tool_registry.execute_tool(
        "get_payment_methods",
        {"user_id": "user123"}
    )
    print(f"   Status: {result.status}")
    if result.status.value == "success":
        print(f"   Métodos encontrados: {result.result['total']}")
    else:
        print(f"   Erro: {result.error_message}")
    print()
    
    # Teste 4: Adicionar método de pagamento
    print("5. Testando AddPaymentMethodTool...")
    result = await tool_registry.execute_tool(
        "add_payment_method",
        {
            "user_id": "user123",
            "method_type": "credit_card",
            "display_name": "Cartão Principal",
            "is_default": True
        }
    )
    print(f"   Status: {result.status}")
    if result.status.value == "success":
        print(f"   Método ID: {result.result['payment_method']['id']}")
    else:
        print(f"   Erro: {result.error_message}")
    print()
    
    # Teste 5: Testar formato OpenAI
    print("6. Testando formato OpenAI...")
    openai_tools = tool_registry.to_openai_format(["check_availability", "book_appointment"])
    print(f"   Tools convertidas: {len(openai_tools)}")
    print(f"   Primeira tool: {openai_tools[0]['function']['name']}")
    print()
    
    # Teste 6: Executar múltiplas tools
    print("7. Testando execução múltipla...")
    from aglib.core.types import ToolCall
    
    tool_calls = [
        ToolCall(id="call1", tool_name="list_services", parameters={}),
        ToolCall(id="call2", tool_name="get_payment_methods", parameters={"user_id": "user123"})
    ]
    
    results = await tool_registry.execute_multiple_tools(tool_calls)
    print(f"   Resultados: {len(results)}")
    for i, result in enumerate(results):
        if hasattr(result, 'status'):
            print(f"   Tool {i+1}: {result.status}")
        else:
            print(f"   Tool {i+1}: erro na execução")
    print()
    
    print("=== Teste Concluído ===")


if __name__ == "__main__":
    asyncio.run(test_tools())