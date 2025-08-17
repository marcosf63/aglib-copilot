from __future__ import annotations
import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging

from .types import (
    ToolDefinition,
    ToolCall,
    ToolResult,
    ToolStatus,
)

logger = logging.getLogger(__name__)


class Tool(ABC):
    """Base class for all tools"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._definition: Optional[ToolDefinition] = None
        self._rate_limiter: Optional[RateLimiter] = None

    @property
    def definition(self) -> ToolDefinition:
        if self._definition is None:
            self._definition = self._create_definition()
        return self._definition

    @abstractmethod
    def _create_definition(self) -> ToolDefinition:
        """Create the tool definition with parameters"""
        pass

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute the tool with given parameters"""
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """Validate parameters against tool definition"""
        errors = []

        for param in self.definition.parameters:
            value = parameters.get(param.name)

            # Check required parameters
            if param.required and value is None:
                errors.append(f"Required parameter '{param.name}' is missing")
                continue

            # Skip validation if parameter is not provided and not required
            if value is None:
                continue

            # Type validation
            if not self._validate_type(value, param.type):
                errors.append(f"Parameter '{param.name}' must be of type {param.type}")

            # Enum validation
            if param.enum and value not in param.enum:
                errors.append(f"Parameter '{param.name}' must be one of: {param.enum}")

        return errors

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        if expected_type not in type_mapping:
            return True  # Unknown type, skip validation

        expected_python_type = type_mapping[expected_type]
        return isinstance(value, expected_python_type)

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert tool definition to OpenAI function calling format"""
        properties = {}
        required = []

        for param in self.definition.parameters:
            prop = {"type": param.type, "description": param.description}

            if param.enum:
                prop["enum"] = param.enum

            if param.format:
                prop["format"] = param.format

            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class RateLimiter:
    """Simple rate limiter for tools"""

    def __init__(self, max_calls: int, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: List[datetime] = []

    def can_execute(self) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)

        # Remove old calls
        self.calls = [call for call in self.calls if call > cutoff]

        return len(self.calls) < self.max_calls

    def record_call(self):
        self.calls.append(datetime.now())


class ToolExecutor:
    """Secure executor for tools"""

    def __init__(self, default_timeout: int = 30):
        self.default_timeout = default_timeout
        self.execution_logs: List[Dict[str, Any]] = []

    async def execute_tool(
        self,
        tool: Tool,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None,
        call_id: Optional[str] = None,
    ) -> ToolResult:
        """Execute a tool safely with validation and timeout"""

        call_id = call_id or str(uuid.uuid4())
        timeout = timeout or tool.definition.timeout or self.default_timeout
        start_time = time.time()

        try:
            # Validate parameters
            validation_errors = tool.validate_parameters(parameters)
            if validation_errors:
                return ToolResult(
                    tool_call_id=call_id,
                    status=ToolStatus.INVALID_PARAMS,
                    error_message="; ".join(validation_errors),
                )

            # Check rate limiting
            if tool._rate_limiter and not tool._rate_limiter.can_execute():
                return ToolResult(
                    tool_call_id=call_id,
                    status=ToolStatus.ERROR,
                    error_message="Rate limit exceeded",
                )

            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    tool.execute(parameters), timeout=timeout
                )

                # Record successful call for rate limiting
                if tool._rate_limiter:
                    tool._rate_limiter.record_call()

                execution_time = time.time() - start_time

                self._log_execution(
                    call_id, tool.name, parameters, "success", execution_time
                )

                return ToolResult(
                    tool_call_id=call_id,
                    status=ToolStatus.SUCCESS,
                    result=result,
                    execution_time=execution_time,
                )

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                self._log_execution(
                    call_id, tool.name, parameters, "timeout", execution_time
                )

                return ToolResult(
                    tool_call_id=call_id,
                    status=ToolStatus.TIMEOUT,
                    error_message=f"Tool execution timed out after {timeout} seconds",
                    execution_time=execution_time,
                )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)

            self._log_execution(
                call_id, tool.name, parameters, "error", execution_time, error_msg
            )
            logger.error(f"Tool execution error: {tool.name} - {error_msg}")

            return ToolResult(
                tool_call_id=call_id,
                status=ToolStatus.ERROR,
                error_message=error_msg,
                execution_time=execution_time,
            )

    def _log_execution(
        self,
        call_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        status: str,
        execution_time: float,
        error_message: Optional[str] = None,
    ):
        """Log tool execution for audit purposes"""
        log_entry = {
            "call_id": call_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "status": status,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "error_message": error_message,
        }

        self.execution_logs.append(log_entry)

        # Keep only last 1000 logs to prevent memory issues
        if len(self.execution_logs) > 1000:
            self.execution_logs = self.execution_logs[-1000:]


class ToolRegistry:
    """Registry for managing available tools"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, List[str]] = {}
        self.executor = ToolExecutor()

    def register(self, tool: Tool, category: str = "general"):
        """Register a tool in the registry"""
        self._tools[tool.name] = tool

        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool.name)

        # Set up rate limiting if specified
        if tool.definition.rate_limit:
            tool._rate_limiter = RateLimiter(tool.definition.rate_limit)

        logger.info(f"Registered tool: {tool.name} in category: {category}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)

    def get_tools_by_category(self, category: str) -> List[Tool]:
        """Get all tools in a category"""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools"""
        return list(self._tools.values())

    def list_tool_names(self) -> List[str]:
        """Get list of all tool names"""
        return list(self._tools.keys())

    def list_categories(self) -> List[str]:
        """Get list of all categories"""
        return list(self._categories.keys())

    def get_tools_for_agent(
        self, agent_type: str, allowed_categories: List[str]
    ) -> List[Tool]:
        """Get tools available for specific agent type"""
        available_tools = []

        for category in allowed_categories:
            if category in self._categories:
                for tool_name in self._categories[category]:
                    if tool_name in self._tools:
                        available_tools.append(self._tools[tool_name])

        return available_tools

    def to_openai_format(self, tool_names: List[str] = None) -> List[Dict[str, Any]]:
        """Convert tools to OpenAI function calling format"""
        tools_to_convert = []

        if tool_names:
            tools_to_convert = [
                self._tools[name] for name in tool_names if name in self._tools
            ]
        else:
            tools_to_convert = list(self._tools.values())

        return [tool.to_openai_format() for tool in tools_to_convert]

    async def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any], call_id: Optional[str] = None
    ) -> ToolResult:
        """Execute a tool by name"""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                tool_call_id=call_id or str(uuid.uuid4()),
                status=ToolStatus.ERROR,
                error_message=f"Tool '{tool_name}' not found",
            )

        return await self.executor.execute_tool(tool, parameters, call_id=call_id)

    async def execute_multiple_tools(
        self, tool_calls: List[ToolCall]
    ) -> List[ToolResult]:
        """Execute multiple tools concurrently"""
        tasks = []

        for tool_call in tool_calls:
            task = self.execute_tool(
                tool_call.tool_name, tool_call.parameters, tool_call.id
            )
            tasks.append(task)

        return await asyncio.gather(*tasks, return_exceptions=True)


# Global tool registry instance
tool_registry = ToolRegistry()


# Utility functions for easy access
def register_tool(tool: Tool, category: str = "general"):
    """Register a tool in the global registry"""
    tool_registry.register(tool, category)


def get_tool(name: str) -> Optional[Tool]:
    """Get a tool from the global registry"""
    return tool_registry.get_tool(name)


async def execute_tool(
    tool_name: str, parameters: Dict[str, Any], call_id: Optional[str] = None
) -> ToolResult:
    """Execute a tool from the global registry"""
    return await tool_registry.execute_tool(tool_name, parameters, call_id)


def get_available_tools_for_llm(tool_names: List[str] = None) -> List[Dict[str, Any]]:
    """Get tools in OpenAI format for LLM integration"""
    return tool_registry.to_openai_format(tool_names)
