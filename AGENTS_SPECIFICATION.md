# Especificação de Agentes - AgLib Copilot

## Visão Geral

Este documento define as responsabilidades, capacidades e tools de cada agente no sistema AgLib Copilot após a integração com LLMs.

## 1. PilotAgent - Agente de Triagem e Roteamento

### Responsabilidades
- **Primeiro contato**: Recepção e análise inicial de todas as mensagens
- **Classificação de intenções**: Identificar o tipo de solicitação do usuário
- **Roteamento inteligente**: Direcionar para o agente especialista adequado
- **Delegação a consultores**: Comunicação direta com consultores especializados
- **Gestão de contexto**: Manter histórico e estado da conversa

### LLM Configuration
- **Model**: GPT-4 Turbo / Claude-3.5 Sonnet
- **Temperature**: 0.3 (equilibrio entre criatividade e precisão)
- **Max Tokens**: 2000
- **System Prompt**: "Especialista em triagem e roteamento de atendimento ao cliente"

### Tools Disponíveis
- `get_customer_profile(user_id)` - Buscar perfil do cliente
- `analyze_intent(message)` - Analisar intenção da mensagem
- `check_agent_availability(agent_type)` - Verificar disponibilidade de agentes
- `log_interaction(user_id, intent, action)` - Registrar interação

### Cenários de Uso
- Saudações e apresentação do sistema
- Análise de pedidos ambíguos ou complexos
- Roteamento para especialistas
- Coordenação entre múltiplos agentes
- Escalação para humanos quando necessário

---

## 2. SchedulingSpecialist - Especialista em Agendamentos

### Responsabilidades
- **Gestão de agenda**: Verificação de disponibilidade e reservas
- **Agendamento de serviços**: Criação, modificação e cancelamento
- **Lembretes**: Envio de notificações e confirmações
- **Otimização**: Sugestão de horários alternativos

### LLM Configuration
- **Model**: GPT-3.5 Turbo (otimizado para eficiência)
- **Temperature**: 0.1 (máxima precisão para datas/horários)
- **Max Tokens**: 1500
- **System Prompt**: "Especialista em agendamentos e gestão de calendário"

### Tools Disponíveis
- `check_availability(date, time, service, duration)` - Verificar disponibilidade
- `book_appointment(user_id, date, time, service, notes)` - Criar agendamento
- `cancel_appointment(appointment_id, reason)` - Cancelar agendamento
- `reschedule_appointment(appointment_id, new_date, new_time)` - Reagendar
- `get_user_appointments(user_id, date_range)` - Buscar agendamentos do usuário
- `send_reminder(appointment_id, type)` - Enviar lembrete
- `suggest_alternatives(preferred_date, service)` - Sugerir horários alternativos
- `block_time_slot(date, time, duration, reason)` - Bloquear horário

### Cenários de Uso
- "Quero agendar um corte para amanhã às 14h"
- "Preciso cancelar meu agendamento de sexta"
- "Tem horário disponível na próxima semana?"
- "Quero remarcar para um dia mais cedo"

---

## 3. PaymentsSpecialist - Especialista em Pagamentos

### Responsabilidades
- **Processamento de pagamentos**: Transações seguras e confiáveis
- **Gestão de métodos**: Cadastro e atualização de formas de pagamento
- **Faturamento**: Geração de faturas e recibos
- **Conciliação**: Verificação de status e histórico financeiro

### LLM Configuration
- **Model**: GPT-3.5 Turbo
- **Temperature**: 0.1 (máxima precisão para valores financeiros)
- **Max Tokens**: 1500
- **System Prompt**: "Especialista em pagamentos e transações financeiras"

### Tools Disponíveis
- `get_payment_methods(user_id)` - Listar métodos de pagamento
- `add_payment_method(user_id, method_data)` - Adicionar método
- `process_payment(amount, currency, method, order_id)` - Processar pagamento
- `check_payment_status(transaction_id)` - Verificar status
- `generate_invoice(order_id, items)` - Gerar fatura
- `send_receipt(transaction_id, email)` - Enviar recibo
- `refund_payment(transaction_id, amount, reason)` - Processar estorno
- `get_transaction_history(user_id, date_range)` - Histórico financeiro

### Cenários de Uso
- "Quero pagar meu agendamento com cartão"
- "Não consegui finalizar o pagamento"
- "Preciso de uma nota fiscal"
- "Quero estornar uma compra"

---

## 4. SupportAgent - Agente de Suporte

### Responsabilidades
- **Suporte técnico**: Resolução de problemas e dúvidas
- **Base de conhecimento**: Acesso a documentação e procedimentos
- **Escalação**: Transferência para especialistas humanos
- **Assistência ao operador**: Integração com CopilotAgent

### LLM Configuration
- **Model**: Claude-3.5 Sonnet (melhor para empatia e comunicação)
- **Temperature**: 0.4 (equilibrio entre precisão e naturalidade)
- **Max Tokens**: 2000
- **System Prompt**: "Agente empático de suporte ao cliente"

### Tools Disponíveis
- `search_kb(query, category)` - Buscar na base de conhecimento
- `get_procedure(procedure_id)` - Obter procedimento específico
- `create_support_ticket(user_id, issue, priority)` - Criar ticket
- `update_ticket_status(ticket_id, status, notes)` - Atualizar ticket
- `escalate_to_human(ticket_id, reason, priority)` - Escalar para humano
- `get_user_tickets(user_id, status)` - Histórico de tickets
- `send_feedback_survey(user_id, ticket_id)` - Enviar pesquisa
- `log_resolution(ticket_id, solution, time_spent)` - Registrar solução

### Cenários de Uso
- "Não consigo acessar minha conta"
- "O app está travando quando tento agendar"
- "Como funciona o sistema de pontos?"
- "Quero fazer uma reclamação"

---

## 5. ImageConsultant - Consultor de Imagens

### Responsabilidades
- **Geração de imagens**: Criação de imagens baseadas em prompts
- **Análise visual**: Interpretação e descrição de imagens
- **Consultoria criativa**: Sugestões de estilos e conceitos
- **Edição básica**: Modificações e ajustes em imagens

### LLM Configuration
- **Model**: GPT-4 Vision / Claude-3.5 Sonnet
- **Temperature**: 0.6 (criatividade moderada)
- **Max Tokens**: 2000
- **System Prompt**: "Consultor criativo especialista em imagens e design"

### Tools Disponíveis
- `generate_image(prompt, style, size, quality)` - Gerar imagem
- `analyze_image(image_url)` - Analisar imagem existente
- `enhance_prompt(basic_prompt, style_preferences)` - Melhorar prompt
- `suggest_styles(theme, occasion)` - Sugerir estilos
- `edit_image(image_url, instructions)` - Editar imagem
- `generate_variations(image_url, count)` - Criar variações
- `compress_image(image_url, quality)` - Otimizar imagem
- `get_image_metadata(image_url)` - Obter metadados

### Cenários de Uso
- "Quero uma imagem de um corte moderno"
- "Gere um logo para minha empresa"
- "Como ficaria este corte em mim?"
- "Preciso de uma imagem para redes sociais"

---

## 6. CopilotAgent - Assistente para Operadores

### Responsabilidades
- **Sugestões em tempo real**: Respostas prontas para operadores humanos
- **Análise de contexto**: Interpretação completa da situação do cliente
- **Busca de informações**: Acesso rápido a dados relevantes
- **Automação de tarefas**: Execução de ações simples

### LLM Configuration
- **Model**: GPT-4 Turbo
- **Temperature**: 0.2 (foco em precisão e utilidade)
- **Max Tokens**: 1500
- **System Prompt**: "Assistente inteligente para operadores de atendimento"

### Tools Disponíveis (Read-Only)
- `get_customer_full_profile(user_id)` - Perfil completo do cliente
- `search_all_kb(query)` - Busca global na base de conhecimento
- `get_similar_cases(issue_description)` - Casos similares
- `suggest_response(context, customer_message)` - Sugerir resposta
- `calculate_metrics(user_id, period)` - Métricas do cliente
- `get_escalation_history(user_id)` - Histórico de escalações
- `analyze_sentiment(message)` - Análise de sentimento
- `predict_next_action(conversation_history)` - Prever próxima ação

### Cenários de Uso
- Operador recebe uma consulta complexa
- Cliente demonstra frustração
- Necessidade de informações técnicas específicas
- Situações que requerem empatia especial

---

## 7. HumanBridge - Ponte para Consultores Humanos

### Responsabilidades
- **Interface humana**: Conexão com consultores especializados
- **Preparação de contexto**: Organização de informações para humanos
- **Monitoramento**: Acompanhamento de interações humanas
- **Fallback**: Alternativa quando automação falha

### LLM Configuration
- **Model**: GPT-3.5 Turbo
- **Temperature**: 0.3
- **Max Tokens**: 1000
- **System Prompt**: "Facilitador de comunicação entre IA e humanos"

### Tools Disponíveis
- `format_context_for_human(conversation_history)` - Formatar contexto
- `notify_human_consultant(user_id, urgency, summary)` - Notificar consultor
- `track_human_response_time(consultant_id)` - Monitorar tempo de resposta
- `escalate_priority(case_id, reason)` - Aumentar prioridade
- `handoff_to_human(user_id, context, specialist_type)` - Transferir para humano
- `get_available_consultants(specialty)` - Consultores disponíveis
- `log_human_interaction(consultant_id, duration, outcome)` - Registrar interação

### Cenários de Uso
- Casos que excedem capacidade da IA
- Solicitações que requerem expertise humana específica
- Situações sensíveis ou de alta complexidade
- Escalações de prioridade máxima

---

## Matriz de Responsabilidades

| Tarefa | Pilot | Scheduling | Payments | Support | ImageConsultant | Copilot | HumanBridge |
|--------|-------|------------|----------|---------|----------------|---------|-------------|
| Triagem inicial | ✓ | | | | | | |
| Agendamentos | → | ✓ | | | | ✓ | |
| Pagamentos | → | | ✓ | | | ✓ | |
| Suporte técnico | → | | | ✓ | | ✓ | → |
| Geração de imagens | → | | | | ✓ | | |
| Assistência a operadores | | | | | | ✓ | |
| Escalação humana | → | → | → | → | → | → | ✓ |
| Análise de contexto | ✓ | | | | | ✓ | |

**Legenda:**
- ✓ = Responsabilidade principal
- → = Roteamento/Escalação para outro agente