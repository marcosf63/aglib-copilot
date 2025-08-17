from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional, List, Union, Callable
from datetime import datetime


class Action(Enum):
    REPLY = auto()
    HANDOFF = auto()
    ESCALATE = auto()
    TO_HUMAN = auto()
    NOOP = auto()
    USE_TOOL = auto()  # New action for tool usage


class ToolStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    INVALID_PARAMS = "invalid_params"


@dataclass
class Message:
    user_id: str
    text: str
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentOutput:
    action: Action
    text: Optional[str] = None
    target_agent: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    tool_calls: List[ToolCall] = field(default_factory=list)  # New field for tool calls
    metadata: Dict[str, Any] = field(default_factory=dict)


# --- Tool System Types ---

@dataclass
class ToolParameter:
    name: str
    type: str  # "string", "integer", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None
    format: Optional[str] = None  # "date", "email", "uri", etc.


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: List[ToolParameter]
    category: str = "general"
    requires_auth: bool = False
    rate_limit: Optional[int] = None  # calls per minute
    timeout: int = 30  # seconds


@dataclass
class ToolCall:
    id: str
    tool_name: str
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass 
class ToolResult:
    tool_call_id: str
    status: ToolStatus
    result: Any = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# --- Enhanced Agent Types ---

@dataclass
class AgentConfig:
    name: str
    llm_provider: str = "openai"
    llm_model: str = "gpt-3.5-turbo"
    temperature: float = 0.3
    max_tokens: Optional[int] = None
    available_tools: List[str] = field(default_factory=list)
    prompt_template: str = "default"
    system_instructions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCapabilities:
    can_use_tools: bool = True
    can_call_llm: bool = True
    can_escalate: bool = True
    can_handoff: bool = True
    max_tool_calls_per_message: int = 5
    allowed_tool_categories: List[str] = field(default_factory=lambda: ["general"])


# --- Copilot contracts (Enhanced) ---

@dataclass
class Suggestion:
    text: str
    confidence: float = 0.5
    actions: Dict[str, Any] = field(default_factory=dict)
    reasoning: Optional[str] = None
    priority: str = "normal"  # "low", "normal", "high", "urgent"
    category: str = "response"  # "response", "action", "escalation", "information"


@dataclass
class CopilotInput:
    message: Message
    session: "Session"  # forward-ref, defined in context.py
    history: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    operator_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CopilotOutput:
    suggestions: List[Suggestion]
    customer_insights: Dict[str, Any] = field(default_factory=dict)
    recommended_actions: List[str] = field(default_factory=list)
    escalation_triggers: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# --- LLM Integration Types ---

@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_estimate: float = 0.0
    model: str = ""
    provider: str = ""


@dataclass
class AgentPerformanceMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    tool_usage_count: Dict[str, int] = field(default_factory=dict)
    llm_usage: LLMUsage = field(default_factory=LLMUsage)
    last_updated: datetime = field(default_factory=datetime.now)


# --- Error Types ---

class AgentError(Exception):
    def __init__(self, message: str, error_code: str = "AGENT_ERROR", agent_name: str = "unknown"):
        super().__init__(message)
        self.error_code = error_code
        self.agent_name = agent_name
        self.timestamp = datetime.now()


class ToolError(Exception):
    def __init__(self, message: str, tool_name: str, error_code: str = "TOOL_ERROR"):
        super().__init__(message)
        self.tool_name = tool_name
        self.error_code = error_code
        self.timestamp = datetime.now()


class LLMError(Exception):
    def __init__(self, message: str, provider: str, model: str, error_code: str = "LLM_ERROR"):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.error_code = error_code
        self.timestamp = datetime.now()


# --- Validation and Security Types ---

@dataclass
class ValidationRule:
    field_name: str
    rule_type: str  # "required", "type", "range", "pattern", "custom"
    rule_value: Any
    error_message: str


@dataclass
class SecurityPolicy:
    rate_limit_per_minute: int = 60
    max_tool_calls_per_session: int = 100
    allowed_domains: List[str] = field(default_factory=list)
    blocked_patterns: List[str] = field(default_factory=list)
    require_authentication: bool = True
    log_all_interactions: bool = True


# --- Event System Types ---

@dataclass
class AgentEvent:
    event_type: str  # "message_received", "tool_called", "error_occurred", etc.
    agent_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    user_id: str = ""


EventHandler = Callable[[AgentEvent], None]


# --- Configuration Types ---

@dataclass
class SystemConfig:
    environment: str = "development"  # "development", "staging", "production"
    debug: bool = False
    enable_metrics: bool = True
    enable_logging: bool = True
    default_llm_provider: str = "openai"
    default_llm_model: str = "gpt-3.5-turbo"
    tool_execution_timeout: int = 30
    max_conversation_history: int = 50
    session_timeout_minutes: int = 60
    security_policy: SecurityPolicy = field(default_factory=SecurityPolicy)


# --- Backward Compatibility Aliases ---

# Keep old names for backward compatibility
AgentMessage = Message
AgentResponse = AgentOutput
