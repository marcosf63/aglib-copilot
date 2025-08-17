# AgLib Copilot 🤖

Uma plataforma avançada de orquestração de agentes inteligentes com integração LLM e sistema de ferramentas completo para automação de atendimento ao cliente.

## 🎯 Visão Geral

O **AgLib Copilot** é um sistema de multi-agentes que orquestra diferentes tipos de inteligência artificial para fornecer atendimento automatizado sofisticado. O sistema combina:

- **Agentes Especializados** com integração LLM (OpenAI, Anthropic, modelos locais)
- **Sistema de Ferramentas** com 20+ tools de negócio
- **Orquestração Inteligente** com roteamento baseado em intenção
- **Suporte Híbrido** com escalação automática para humanos
- **Monitoramento e Métricas** em tempo real

### Arquitetura dos Agentes

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Pilot    │◄──►│   Specialists   │◄──►│     Support     │
│  (Router)   │    │ - Scheduling    │    │ - Human Bridge  │
│             │    │ - Payments      │    │ - Copilot       │
└─────────────┘    │ - Consultants   │    └─────────────────┘
                   └─────────────────┘
```

## ✨ Funcionalidades

### 🧠 Integração LLM Multi-Provider
- **OpenAI GPT**: Modelos GPT-3.5 e GPT-4
- **Anthropic Claude**: Suporte completo para Claude
- **Modelos Locais**: Integração com Ollama
- **Fallback Inteligente**: Sistema robusto de recuperação

### 🛠️ Sistema de Ferramentas
- **Agendamentos**: 6 tools (verificar disponibilidade, agendar, cancelar, etc.)
- **Pagamentos**: 7 tools (processar pagamento, gerar fatura, métodos de pagamento)
- **CRM**: 7 tools (perfil do cliente, histórico, tickets de suporte)
- **Execução Concorrente**: Múltiplas ferramentas em paralelo
- **Validação de Segurança**: Rate limiting e sanitização

### 🎯 Agentes Especializados
- **Pilot Agent**: Roteamento inteligente e análise de intenção
- **Scheduling Specialist**: Especialista em agendamentos
- **Payments Specialist**: Processamento de pagamentos
- **Image Consultant**: Geração e análise de imagens
- **Support Agent**: Suporte humano com sugestões do Copilot
- **Human Bridge**: Escalação para consultores humanos

### 📊 Monitoramento e Métricas
- **Métricas de Performance**: Tempo de resposta, taxa de sucesso
- **Uso de LLM**: Contagem de tokens, custos estimados
- **Estatísticas de Tools**: Ferramentas mais utilizadas
- **Logs Estruturados**: Rastreamento completo de interações

## 🚀 Instalação

### Pré-requisitos
- Python 3.10+
- Chaves de API LLM (opcional, funciona em modo fallback)

### Setup Básico

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/aglib-copilot-consultat.git
cd aglib-copilot-consultat

# Crie ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Instale dependências
pip install -e .

# Para desenvolvimento
pip install -e ".[dev]"
```

### Configuração das APIs

```bash
# OpenAI (opcional)
export OPENAI_API_KEY="sua_chave_openai"

# Anthropic (opcional)
export ANTHROPIC_API_KEY="sua_chave_anthropic"

# Para modelos locais via Ollama
# Instale o Ollama e configure modelos localmente
```

## 📖 Uso Rápido

### Exemplo Básico

```python
import asyncio
from aglib.core.registry import AgentRegistry
from aglib.core.routing import Router
from aglib.core.types import Message
from aglib.core.context import Session
from aglib.agents.pilot import PilotAgent

async def main():
    # Setup básico
    pilot = PilotAgent("Pilot")
    registry = AgentRegistry().add(pilot)
    router = Router(registry)
    session = Session(user_id="user123", channel="web")
    
    # Processar mensagem
    message = Message("user123", "Olá! Quero agendar um horário")
    result = await router.dispatch("Pilot", message, session)
    
    print(f"Resposta: {result.text}")
    print(f"Ação: {result.action}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Demonstração Completa

```bash
# Exemplo básico (sem LLM)
python examples/quickstart.py

# Exemplo com LLM e tools
python examples/llm_quickstart.py

# Teste do sistema de tools
python test_tools.py
```

## 🔧 Configuração Avançada

### Personalização de Agentes

```python
from aglib.agents.base import BaseAgent
from aglib.core.types import AgentConfig, AgentCapabilities

class CustomAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            llm_model="gpt-4",
            max_tokens=1000,
            temperature=0.7
        )
        capabilities = AgentCapabilities(
            can_call_llm=True,
            can_use_tools=True,
            can_escalate=True
        )
        super().__init__("CustomAgent", config, capabilities)
    
    async def _handle_with_llm(self, msg, session):
        # Lógica personalizada com LLM
        pass
    
    async def _handle_without_llm(self, msg, session):
        # Fallback sem LLM
        pass
```

### Criação de Tools Customizadas

```python
from aglib.core.tools import Tool, ToolResult, ToolStatus

class CustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="Ferramenta personalizada",
            category="custom"
        )
    
    async def execute(self, parameters):
        # Implementar lógica
        return ToolResult(
            status=ToolStatus.SUCCESS,
            result={"message": "Sucesso!"}
        )

# Registrar tool
from aglib.core.tools import tool_registry
tool_registry.register(CustomTool())
```

## 📚 Documentação da API

### Agentes Principais

#### PilotAgent
Agente principal responsável pelo roteamento inteligente de mensagens.

```python
pilot = PilotAgent(
    name="Pilot",
    consultants=consultant_hub,  # Opcional
    config=custom_config         # Opcional
)
```

#### SchedulingSpecialist
Especialista em operações de agendamento.

**Tools disponíveis:**
- `check_availability`: Verificar disponibilidade
- `book_appointment`: Agendar compromisso
- `cancel_appointment`: Cancelar agendamento
- `reschedule_appointment`: Reagendar
- `list_appointments`: Listar agendamentos
- `list_services`: Listar serviços

#### PaymentsSpecialist
Especialista em processamento de pagamentos.

**Tools disponíveis:**
- `process_payment`: Processar pagamento
- `refund_payment`: Estornar pagamento
- `get_payment_methods`: Listar métodos de pagamento
- `add_payment_method`: Adicionar método
- `generate_invoice`: Gerar fatura
- `get_transaction_history`: Histórico de transações
- `validate_payment_info`: Validar informações

### Sistema de Tools

```python
from aglib.core.tools import tool_registry

# Executar tool
result = await tool_registry.execute_tool(
    "check_availability",
    {"date": "2025-08-18", "service": "corte_masculino"}
)

# Executar múltiplas tools
results = await tool_registry.execute_multiple_tools([
    ToolCall(id="1", tool_name="tool1", parameters={}),
    ToolCall(id="2", tool_name="tool2", parameters={})
])

# Converter para formato OpenAI
openai_tools = tool_registry.to_openai_format(["tool1", "tool2"])
```

### Contexto e Sessão

```python
from aglib.core.context import Session, CustomerProfile, BusinessContext

# Criar sessão com contexto de negócio
session = Session(user_id="user123", channel="web")

# Adicionar perfil do cliente
session.business_context.customer_profile = CustomerProfile(
    user_id="user123",
    name="João Silva",
    email="joao@email.com",
    tier="vip"
)

# Adicionar histórico
session.business_context.order_history = [
    {"id": "order1", "total": 45.00, "service": "corte_masculino"}
]
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Testes específicos
pytest tests/test_agents.py
pytest tests/test_tools.py

# Testes com cobertura
pytest --cov=aglib

# Testes assíncronos
pytest --asyncio-mode=auto
```

## 🔒 Segurança

### Validação de Entrada
- Sanitização automática de parâmetros
- Validação de tipos com Pydantic
- Rate limiting por usuário

### Proteção de APIs
- Chaves de API em variáveis de ambiente
- Timeout configurável para requisições
- Retry automático com backoff exponencial

### Logs e Auditoria
- Logging estruturado de todas as interações
- Métricas de segurança e performance
- Rastreamento de uso de tokens LLM

## 📊 Monitoramento

### Métricas Disponíveis

```python
# Obter métricas do agente
metrics = agent.get_metrics()
print(f"Total de requisições: {metrics.total_requests}")
print(f"Taxa de sucesso: {metrics.success_rate:.2%}")
print(f"Tempo médio: {metrics.average_response_time:.2f}s")
print(f"Tokens utilizados: {metrics.llm_usage.total_tokens}")
```

### Dashboard de Métricas
- Performance por agente
- Uso de ferramentas
- Custos de LLM
- Latência e throughput

## 🛣️ Roadmap

### Versão 0.2.0
- [ ] Interface web para monitoramento
- [ ] Suporte a webhooks
- [ ] Cache inteligente de respostas
- [ ] Integração com mais provedores LLM

### Versão 0.3.0
- [ ] Sistema de plugins
- [ ] Analytics avançado
- [ ] Suporte a streaming
- [ ] Modo offline melhorado

## 🤝 Contribuição

### Como Contribuir

1. **Fork** o projeto
2. **Crie** uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. **Commit** suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. **Push** para a branch (`git push origin feature/nova-feature`)
5. **Abra** um Pull Request

### Padrões de Código

```bash
# Formatação
black .
ruff check . --fix

# Type checking
mypy aglib/

# Testes
pytest --cov=aglib
```

### Estrutura de Commits
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Documentação
- `style:` Formatação
- `refactor:` Refatoração
- `test:` Testes

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/marcosf63/aglib-copilot-consultat/issues)
- **Discussões**: [GitHub Discussions](https://github.com/marcosf63/aglib-copilot-consultat/discussions)
- **Email**: marcosf63@gmail.com

## 🙏 Reconhecimentos

- OpenAI pela API GPT
- Anthropic pela API Claude
- Comunidade Python pelas bibliotecas utilizadas
- Todos os contribuidores do projeto

---

**Desenvolvido com ❤️ pela equipe AgLib**

*Transformando atendimento ao cliente com inteligência artificial*