from __future__ import annotations
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from ..core.types import (
    Message,
    AgentOutput,
    Action,
    AgentConfig,
    AgentCapabilities,
    ToolCall,
    ToolResult,
    AgentPerformanceMetrics,
)
from ..core.context import Session
from ..adapters.llm import LLMAdapter, LLMFactory, LLMMessage, LLMRequest
from ..core.prompts import render_prompt
from ..core.tools import tool_registry

logger = logging.getLogger(__name__)


class Agent(ABC):
    def __init__(
        self,
        name: Optional[str] = None,
        config: Optional[AgentConfig] = None,
        capabilities: Optional[AgentCapabilities] = None,
    ):
        self.name = name or self.__class__.__name__
        self.config = config or AgentConfig(name=self.name)
        self.capabilities = capabilities or AgentCapabilities()

        # LLM integration
        self.llm: Optional[LLMAdapter] = None
        if self.capabilities.can_call_llm:
            self._initialize_llm()

        # Performance tracking
        self.metrics = AgentPerformanceMetrics()

        # Available tools
        self.available_tools: List[str] = []
        if self.capabilities.can_use_tools:
            self._setup_tools()

    def _initialize_llm(self):
        """Initialize LLM adapter"""
        try:
            self.llm = LLMFactory.create(
                provider=self.config.llm_provider,
                model=self.config.llm_model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            logger.info(
                f"LLM initialized for agent {self.name}: {self.config.llm_model}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM for agent {self.name}: {e}")
            self.capabilities.can_call_llm = False

    def _setup_tools(self):
        """Setup available tools for this agent"""
        self.available_tools = self.config.available_tools.copy()

        # Get tools by category if specified in capabilities
        for category in self.capabilities.allowed_tool_categories:
            category_tools = tool_registry.get_tools_by_category(category)
            for tool in category_tools:
                if tool.name not in self.available_tools:
                    self.available_tools.append(tool.name)

        logger.info(
            f"Agent {self.name} has {len(self.available_tools)} tools available"
        )

    async def handle(self, msg: Message, session: Session) -> AgentOutput:
        """Main handler method - updated to include LLM and tools integration"""
        start_time = time.time()
        self.metrics.total_requests += 1

        try:
            # Add message to session history
            session.add_message("user", msg.text, agent=self.name)

            # Get response from agent implementation
            if self.capabilities.can_call_llm and self.llm:
                result = await self._handle_with_llm(msg, session)
            else:
                result = await self._handle_without_llm(msg, session)

            # Add agent response to session history
            if result.text:
                session.add_message("assistant", result.text, agent=self.name)

            # Update metrics
            self.metrics.successful_requests += 1
            execution_time = time.time() - start_time
            self._update_metrics(execution_time)

            return result

        except Exception as e:
            # Update error metrics
            self.metrics.failed_requests += 1
            execution_time = time.time() - start_time
            self._update_metrics(execution_time)

            logger.error(f"Error in agent {self.name}: {e}")

            return AgentOutput(
                action=Action.REPLY,
                text="Desculpe, ocorreu um erro interno. Tente novamente ou entre em contato com o suporte.",
                metadata={"error": str(e), "agent": self.name},
            )

    async def _handle_with_llm(self, msg: Message, session: Session) -> AgentOutput:
        """Handle message using LLM"""
        try:
            # Get context for this agent type
            context = session.get_context_for_agent(self.name.lower())

            # Render prompt template
            messages = render_prompt(
                agent_type=self.name.lower(), user_message=msg.text, **context
            )

            # Convert to LLM format
            llm_messages = [
                LLMMessage(role=m["role"], content=m["content"]) for m in messages
            ]

            # Prepare LLM request
            llm_request = LLMRequest(
                messages=llm_messages,
                model=self.config.llm_model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            # Add tools if available and agent can use them
            if self.capabilities.can_use_tools and self.available_tools:
                llm_request.tools = tool_registry.to_openai_format(self.available_tools)

            # Call LLM
            llm_response = await self.llm.complete(llm_request)

            # Update LLM usage metrics
            self._update_llm_metrics(llm_response.usage)

            # Handle tool calls if present
            tool_results = []
            if llm_response.tool_calls and self.capabilities.can_use_tools:
                tool_results = await self._execute_tools(llm_response.tool_calls)

            # Process LLM response into AgentOutput
            return await self._process_llm_response(
                llm_response, tool_results, msg, session
            )

        except Exception as e:
            logger.error(f"LLM error in agent {self.name}: {e}")
            # Fallback to non-LLM handling
            return await self._handle_without_llm(msg, session)

    async def _execute_tools(
        self, tool_calls: List[Dict[str, Any]]
    ) -> List[ToolResult]:
        """Execute tool calls from LLM"""
        results = []
        executed_count = 0

        for tool_call_data in tool_calls:
            # Respect tool call limits
            if executed_count >= self.capabilities.max_tool_calls_per_message:
                logger.warning(f"Agent {self.name} exceeded max tool calls limit")
                break

            try:
                # Parse tool call
                tool_call = ToolCall(
                    id=tool_call_data.get("id", str(uuid.uuid4())),
                    tool_name=tool_call_data["function"],
                    parameters=(
                        json.loads(tool_call_data["arguments"])
                        if isinstance(tool_call_data["arguments"], str)
                        else tool_call_data["arguments"]
                    ),
                )

                # Execute tool
                result = await tool_registry.execute_tool(
                    tool_call.tool_name, tool_call.parameters, tool_call.id
                )

                results.append(result)
                executed_count += 1

                # Update tool usage metrics
                if tool_call.tool_name not in self.metrics.tool_usage_count:
                    self.metrics.tool_usage_count[tool_call.tool_name] = 0
                self.metrics.tool_usage_count[tool_call.tool_name] += 1

            except Exception as e:
                logger.error(f"Tool execution error in agent {self.name}: {e}")
                # Continue with other tools
                continue

        return results

    async def _process_llm_response(
        self,
        llm_response,
        tool_results: List[ToolResult],
        msg: Message,
        session: Session,
    ) -> AgentOutput:
        """Process LLM response and convert to AgentOutput"""

        # If there are tool calls, we might need to call LLM again with results
        if tool_results:
            return await self._handle_tool_results(
                llm_response, tool_results, msg, session
            )

        # No tool calls, just return the response
        response_text = llm_response.content.strip()

        # Analyze response to determine action
        action = self._determine_action(response_text, session)

        return AgentOutput(
            action=action,
            text=response_text,
            metadata={
                "agent": self.name,
                "llm_model": self.config.llm_model,
                "llm_usage": llm_response.usage,
            },
        )

    async def _handle_tool_results(
        self,
        llm_response,
        tool_results: List[ToolResult],
        msg: Message,
        session: Session,
    ) -> AgentOutput:
        """Handle tool execution results and potentially call LLM again"""

        # Prepare tool results for LLM
        tool_messages = []
        for result in tool_results:
            if result.status.value == "success":
                content = (
                    f"Tool {result.tool_call_id} executed successfully: {result.result}"
                )
            else:
                content = f"Tool {result.tool_call_id} failed: {result.error_message}"

            tool_messages.append(LLMMessage(role="system", content=content))

        # Add tool results and ask LLM to synthesize final response
        synthesis_prompt = LLMMessage(
            role="user",
            content="Com base nos resultados das ferramentas acima, forneça uma resposta final para o usuário.",
        )

        # Call LLM again for synthesis
        synthesis_request = LLMRequest(
            messages=[llm_response] + tool_messages + [synthesis_prompt],
            model=self.config.llm_model,
            temperature=self.config.temperature,
        )

        try:
            final_response = await self.llm.complete(synthesis_request)
            self._update_llm_metrics(final_response.usage)

            return AgentOutput(
                action=Action.REPLY,
                text=final_response.content.strip(),
                tool_calls=[],  # Tool calls already executed
                metadata={
                    "agent": self.name,
                    "tools_used": [r.tool_call_id for r in tool_results],
                    "llm_model": self.config.llm_model,
                },
            )

        except Exception as e:
            logger.error(f"Tool synthesis error in agent {self.name}: {e}")

            # Fallback: create response based on tool results
            successful_tools = [r for r in tool_results if r.status.value == "success"]
            if successful_tools:
                response_text = "Consegui processar sua solicitação com sucesso."
            else:
                response_text = "Houve alguns problemas ao processar sua solicitação. Tente novamente."

            return AgentOutput(
                action=Action.REPLY,
                text=response_text,
                metadata={"agent": self.name, "tool_synthesis_failed": True},
            )

    def _determine_action(self, response_text: str, session: Session) -> Action:
        """Determine the appropriate action based on response content"""
        response_lower = response_text.lower()

        # Check for escalation keywords
        if any(
            keyword in response_lower
            for keyword in ["escalar", "supervisor", "gerente", "não consigo"]
        ):
            return Action.ESCALATE

        # Check for handoff keywords
        if any(
            keyword in response_lower
            for keyword in ["especialista", "transferir", "encaminhar"]
        ):
            return Action.HANDOFF

        # Check for human bridge keywords
        if any(
            keyword in response_lower for keyword in ["humano", "pessoa", "atendente"]
        ):
            return Action.TO_HUMAN

        # Default to reply
        return Action.REPLY

    def _update_metrics(self, execution_time: float):
        """Update performance metrics"""
        # Update average response time
        total_requests = self.metrics.total_requests
        current_avg = self.metrics.average_response_time

        self.metrics.average_response_time = (
            (current_avg * (total_requests - 1)) + execution_time
        ) / total_requests

        self.metrics.last_updated = time.time()

    def _update_llm_metrics(self, usage: Dict[str, int]):
        """Update LLM usage metrics"""
        self.metrics.llm_usage.prompt_tokens += usage.get("prompt_tokens", 0)
        self.metrics.llm_usage.completion_tokens += usage.get("completion_tokens", 0)
        self.metrics.llm_usage.total_tokens += usage.get("total_tokens", 0)
        self.metrics.llm_usage.model = self.config.llm_model
        self.metrics.llm_usage.provider = self.config.llm_provider

    @abstractmethod
    async def _handle_without_llm(self, msg: Message, session: Session) -> AgentOutput:
        """Fallback handler when LLM is not available - must be implemented by subclasses"""
        raise NotImplementedError

    def get_metrics(self) -> AgentPerformanceMetrics:
        """Get current performance metrics"""
        return self.metrics

    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return self.available_tools.copy()

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if agent can use a specific tool"""
        return tool_name in self.available_tools
