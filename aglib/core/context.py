from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class ConversationMessage:
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "agent": self.agent,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConversationMessage:
        timestamp = datetime.fromisoformat(data["timestamp"])
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=timestamp,
            agent=data.get("agent"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ConversationHistory:
    messages: List[ConversationMessage] = field(default_factory=list)
    max_messages: int = 50

    def add_message(
        self, role: str, content: str, agent: Optional[str] = None, **metadata
    ):
        message = ConversationMessage(
            role=role, content=content, agent=agent, metadata=metadata
        )
        self.messages.append(message)

        # Keep only the last max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def get_recent_messages(self, count: int = 10) -> List[ConversationMessage]:
        return self.messages[-count:] if count < len(self.messages) else self.messages

    def get_messages_by_agent(self, agent: str) -> List[ConversationMessage]:
        return [msg for msg in self.messages if msg.agent == agent]

    def get_last_user_message(self) -> Optional[ConversationMessage]:
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg
        return None

    def to_llm_format(self, include_system: bool = False) -> List[Dict[str, str]]:
        """Convert to format suitable for LLM APIs"""
        result = []
        for msg in self.messages:
            if not include_system and msg.role == "system":
                continue
            result.append({"role": msg.role, "content": msg.content})
        return result

    def clear(self):
        self.messages.clear()


@dataclass
class CustomerProfile:
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    tier: str = "regular"  # regular, vip, premium
    created_at: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_context_string(self) -> str:
        """Convert to string for LLM context"""
        context = f"Cliente: {self.name or 'N/A'} (ID: {self.user_id})"
        if self.tier != "regular":
            context += f" - Nível: {self.tier.upper()}"
        if self.preferences:
            prefs = ", ".join(f"{k}: {v}" for k, v in self.preferences.items())
            context += f" - Preferências: {prefs}"
        return context


@dataclass
class BusinessContext:
    customer_profile: Optional[CustomerProfile] = None
    order_history: List[Dict[str, Any]] = field(default_factory=list)
    support_tickets: List[Dict[str, Any]] = field(default_factory=list)
    appointments: List[Dict[str, Any]] = field(default_factory=list)
    payments: List[Dict[str, Any]] = field(default_factory=list)
    knowledge_base_entries: List[Dict[str, Any]] = field(default_factory=list)

    def get_customer_summary(self) -> str:
        if not self.customer_profile:
            return "Cliente novo ou perfil não encontrado"

        summary = self.customer_profile.to_context_string()

        if self.order_history:
            summary += f" - {len(self.order_history)} pedidos anteriores"

        if self.support_tickets:
            open_tickets = len(
                [t for t in self.support_tickets if t.get("status") == "open"]
            )
            if open_tickets > 0:
                summary += f" - {open_tickets} tickets em aberto"

        if self.appointments:
            upcoming = len(
                [a for a in self.appointments if a.get("status") == "scheduled"]
            )
            if upcoming > 0:
                summary += f" - {upcoming} agendamentos futuros"

        return summary

    def get_relevant_context(self, topic: str) -> str:
        """Get relevant context based on conversation topic"""
        context_parts = []

        # Always include customer summary
        context_parts.append(self.get_customer_summary())

        # Topic-specific context
        if "agend" in topic.lower() and self.appointments:
            recent_appointments = self.appointments[-3:]  # Last 3 appointments
            context_parts.append(
                f"Agendamentos recentes: {len(recent_appointments)} encontrados"
            )

        if "pagam" in topic.lower() and self.payments:
            recent_payments = self.payments[-3:]
            context_parts.append(
                f"Pagamentos recentes: {len(recent_payments)} encontrados"
            )

        if "suporte" in topic.lower() and self.support_tickets:
            open_tickets = [
                t for t in self.support_tickets if t.get("status") == "open"
            ]
            context_parts.append(f"Tickets de suporte: {len(open_tickets)} em aberto")

        return " | ".join(context_parts)


@dataclass
class SessionState:
    variables: Dict[str, Any] = field(default_factory=dict)
    flags: Dict[str, bool] = field(default_factory=dict)
    temp_data: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any):
        self.variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def flag(self, name: str, value: bool = True):
        self.flags[name] = value

    def is_flagged(self, name: str) -> bool:
        return self.flags.get(name, False)

    def store_temp(self, key: str, value: Any, ttl_minutes: int = 30):
        """Store temporary data with TTL"""
        self.temp_data[key] = {
            "value": value,
            "expires_at": datetime.now().timestamp() + (ttl_minutes * 60),
        }

    def get_temp(self, key: str, default: Any = None) -> Any:
        if key not in self.temp_data:
            return default

        entry = self.temp_data[key]
        if datetime.now().timestamp() > entry["expires_at"]:
            del self.temp_data[key]
            return default

        return entry["value"]

    def cleanup_expired(self):
        """Remove expired temporary data"""
        now = datetime.now().timestamp()
        expired_keys = [
            key for key, entry in self.temp_data.items() if now > entry["expires_at"]
        ]
        for key in expired_keys:
            del self.temp_data[key]


@dataclass
class Session:
    user_id: str
    channel: str
    state: Dict[str, Any] = field(default_factory=dict)  # Backward compatibility
    last_agent: Optional[str] = None

    # Enhanced context management
    conversation_history: ConversationHistory = field(
        default_factory=ConversationHistory
    )
    business_context: BusinessContext = field(default_factory=BusinessContext)
    session_state: SessionState = field(default_factory=SessionState)

    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def update_activity(self):
        self.last_activity = datetime.now()
        self.session_state.cleanup_expired()

    def add_message(
        self, role: str, content: str, agent: Optional[str] = None, **metadata
    ):
        self.conversation_history.add_message(role, content, agent, **metadata)
        self.update_activity()

    def get_context_for_agent(self, agent_type: str) -> Dict[str, Any]:
        """Get context optimized for specific agent type"""
        self.update_activity()

        last_message = self.conversation_history.get_last_user_message()
        topic = last_message.content if last_message else ""

        return {
            "user_context": self.business_context.get_customer_summary(),
            "conversation_history": self._format_conversation_history(),
            "current_topic": topic,
            "relevant_context": self.business_context.get_relevant_context(topic),
            "session_flags": dict(self.session_state.flags),
            "agent_type": agent_type,
        }

    def _format_conversation_history(self, max_messages: int = 6) -> str:
        """Format recent conversation for LLM context"""
        recent_messages = self.conversation_history.get_recent_messages(max_messages)
        if not recent_messages:
            return "Início da conversa"

        formatted = []
        for msg in recent_messages:
            role_label = {"user": "Cliente", "assistant": "Assistente"}.get(
                msg.role, msg.role
            )
            agent_info = f" ({msg.agent})" if msg.agent else ""
            formatted.append(f"{role_label}{agent_info}: {msg.content}")

        return "\n".join(formatted)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session for storage"""
        return {
            "user_id": self.user_id,
            "channel": self.channel,
            "state": self.state,
            "last_agent": self.last_agent,
            "conversation_history": [
                msg.to_dict() for msg in self.conversation_history.messages
            ],
            "business_context": {
                "customer_profile": (
                    self.business_context.customer_profile.__dict__
                    if self.business_context.customer_profile
                    else None
                ),
                "order_history": self.business_context.order_history,
                "support_tickets": self.business_context.support_tickets,
                "appointments": self.business_context.appointments,
                "payments": self.business_context.payments,
            },
            "session_state": {
                "variables": self.session_state.variables,
                "flags": self.session_state.flags,
                "temp_data": self.session_state.temp_data,
            },
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Session:
        """Deserialize session from storage"""
        session = cls(
            user_id=data["user_id"],
            channel=data["channel"],
            state=data.get("state", {}),
            last_agent=data.get("last_agent"),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
        )

        # Restore conversation history
        if "conversation_history" in data:
            for msg_data in data["conversation_history"]:
                msg = ConversationMessage.from_dict(msg_data)
                session.conversation_history.messages.append(msg)

        # Restore business context
        if "business_context" in data:
            bc_data = data["business_context"]
            session.business_context = BusinessContext(
                customer_profile=(
                    CustomerProfile(**bc_data["customer_profile"])
                    if bc_data.get("customer_profile")
                    else None
                ),
                order_history=bc_data.get("order_history", []),
                support_tickets=bc_data.get("support_tickets", []),
                appointments=bc_data.get("appointments", []),
                payments=bc_data.get("payments", []),
            )

        # Restore session state
        if "session_state" in data:
            ss_data = data["session_state"]
            session.session_state = SessionState(
                variables=ss_data.get("variables", {}),
                flags=ss_data.get("flags", {}),
                temp_data=ss_data.get("temp_data", {}),
            )

        return session
