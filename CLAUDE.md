# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Basic example (fallback mode)
python examples/quickstart.py

# LLM-powered example (requires API keys)
python examples/llm_quickstart.py

# Test tools system
python test_tools.py
```

### Environment Setup
```bash
# Create virtual environment in .venv with aglib prompt
python -m venv .venv --prompt aglib
source .venv/bin/activate
pip install -e .

# For LLM integration, set API keys:
export OPENAI_API_KEY=your_openai_key
# OR
export ANTHROPIC_API_KEY=your_anthropic_key
```

### Code Quality
```bash
# Linting with ruff (configured with line-length = 100)
ruff check .

# Type checking with mypy
mypy aglib/
```

## Architecture Overview

This is `aglib-copilot`, a sophisticated multi-agent orchestration system with LLM integration and tools. It implements intelligent conversational agents with specialized roles, tool usage capabilities, and human-in-the-loop support.

### Core Components

**Agent System**: All agents inherit from enhanced `Agent` base class with:
- LLM integration (OpenAI, Anthropic, Local models)
- Tool execution capabilities
- Performance metrics tracking
- Fallback handling for reliability

**LLM Integration**: Unified adapter system (`aglib/adapters/llm.py`) supporting multiple providers with automatic fallbacks and error handling.

**Tools System**: Comprehensive tool framework (`aglib/core/tools.py`) with:
- Security validation and rate limiting
- Concurrent execution support
- OpenAI function calling format compatibility
- Audit logging

**Context Management**: Enhanced session tracking with conversation history, customer profiles, and business context.

### Agent Hierarchy

1. **PilotAgent**: LLM-powered entry point with CRM tools for intelligent triaging and routing
2. **SchedulingSpecialist**: Manages appointments using scheduling tools
3. **PaymentsSpecialist**: Handles financial transactions with payment tools
4. **SupportAgent**: Provides technical support with knowledge base and CRM tools
5. **ImageConsultant**: Generates images (extensible for real image generation APIs)
6. **CopilotAgent**: AI assistant for human operators with read-only access to all tools
7. **HumanBridge**: Interface for complex cases requiring human expertise

### Available Tools

**Scheduling Tools** (`aglib/tools/scheduling.py`):
- `check_availability`: Check time slot availability
- `book_appointment`: Create new appointments
- `cancel_appointment`: Cancel existing appointments
- `reschedule_appointment`: Modify appointment times
- `get_user_appointments`: Retrieve user's appointments
- `list_services`: Show available services

**Payment Tools** (`aglib/tools/payments.py`):
- `get_payment_methods`: List user payment methods
- `add_payment_method`: Add new payment method
- `process_payment`: Process transactions
- `check_payment_status`: Verify payment status
- `generate_invoice`: Create invoices
- `refund_payment`: Process refunds
- `get_transaction_history`: Retrieve transaction history

**CRM Tools** (`aglib/tools/crm.py`):
- `get_customer_profile`: Retrieve customer information
- `update_customer_info`: Modify customer data
- `get_order_history`: Show purchase history
- `create_support_ticket`: Create support tickets
- `get_user_tickets`: Retrieve support tickets
- `get_customer_insights`: Generate customer analytics
- `log_interaction`: Record customer interactions

### Key Patterns

**LLM-Powered Intelligence**: Agents use configured LLMs for natural language understanding and response generation, with automatic fallback to rule-based responses.

**Tool-Augmented Capabilities**: Agents can execute tools to perform real actions (booking, payments, data retrieval) based on conversation context.

**Prompt Engineering**: Sophisticated prompt templates (`aglib/core/prompts.py`) with context injection, few-shot examples, and role-specific instructions.

**Performance Monitoring**: Built-in metrics tracking for requests, response times, LLM usage, and tool execution statistics.

**Error Recovery**: Multiple layers of fallback handling to ensure system reliability even when LLMs or external services fail.

### Project Structure
- `aglib/core/`: Core types, routing, registry, context management, tools framework, prompts
- `aglib/agents/`: Agent implementations with LLM integration
- `aglib/adapters/`: LLM adapters for OpenAI, Anthropic, local models
- `aglib/tools/`: Domain-specific tool implementations
- `aglib/policies/`: Routing and handoff decision logic
- `examples/`: Demonstration scripts showing both basic and LLM-powered usage

### Configuration

**Agent Configuration**: Each agent can be configured with:
- LLM provider and model
- Temperature and token limits
- Available tools and categories
- Capabilities and security settings

**Environment Variables**:
- `OPENAI_API_KEY`: OpenAI API access
- `ANTHROPIC_API_KEY`: Anthropic API access  
- `LOCAL_LLM_URL`: Local model endpoint (default: http://localhost:11434)

## Requirements
- Python 3.10+
- Dependencies: OpenAI, Anthropic, Pydantic, HTTPX, tiktoken, python-dotenv
- Optional: Local LLM server (Ollama) for offline operation