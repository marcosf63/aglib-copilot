from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import random

from ..core.tools import Tool
from ..core.types import ToolDefinition, ToolParameter
from ..core.context import CustomerProfile


# Mock CRM database for development
class MockCRMDatabase:
    def __init__(self):
        self.customers: Dict[str, Dict] = {}
        self.orders: Dict[str, List[Dict]] = {}
        self.support_tickets: Dict[str, List[Dict]] = {}
        self.interactions: Dict[str, List[Dict]] = {}
        
        # Initialize with some demo data
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize with demo customer data"""
        demo_customers = [
            {
                "user_id": "user123",
                "name": "João Silva",
                "email": "joao.silva@email.com",
                "phone": "(11) 99999-1234",
                "tier": "vip",
                "preferences": {"preferred_time": "morning", "favorite_service": "corte_masculino"},
                "created_at": (datetime.now() - timedelta(days=180)).isoformat(),
                "last_interaction": (datetime.now() - timedelta(days=2)).isoformat(),
                "total_spent": 450.00,
                "visit_count": 12
            },
            {
                "user_id": "user456", 
                "name": "Maria Santos",
                "email": "maria.santos@email.com",
                "phone": "(11) 98888-5678",
                "tier": "premium",
                "preferences": {"preferred_time": "afternoon", "favorite_service": "coloracao"},
                "created_at": (datetime.now() - timedelta(days=90)).isoformat(),
                "last_interaction": (datetime.now() - timedelta(days=7)).isoformat(),
                "total_spent": 890.00,
                "visit_count": 8
            }
        ]
        
        for customer in demo_customers:
            self.customers[customer["user_id"]] = customer
            
            # Add some demo orders
            self.orders[customer["user_id"]] = [
                {
                    "id": str(uuid.uuid4()),
                    "date": (datetime.now() - timedelta(days=30)).isoformat(),
                    "services": ["corte_masculino"],
                    "total_amount": 45.00,
                    "status": "completed"
                },
                {
                    "id": str(uuid.uuid4()),
                    "date": (datetime.now() - timedelta(days=60)).isoformat(),
                    "services": ["corte_masculino", "barba"],
                    "total_amount": 70.00,
                    "status": "completed"
                }
            ]
            
            # Add demo support tickets
            self.support_tickets[customer["user_id"]] = [
                {
                    "id": str(uuid.uuid4()),
                    "subject": "Dúvida sobre horários",
                    "description": "Gostaria de saber se vocês atendem aos domingos",
                    "status": "closed",
                    "priority": "low",
                    "created_at": (datetime.now() - timedelta(days=15)).isoformat(),
                    "updated_at": (datetime.now() - timedelta(days=14)).isoformat()
                }
            ]

    def get_customer_profile(self, user_id: str) -> Optional[Dict]:
        """Get customer profile"""
        return self.customers.get(user_id)

    def update_customer_info(self, user_id: str, data: Dict) -> Dict:
        """Update customer information"""
        if user_id not in self.customers:
            # Create new customer
            self.customers[user_id] = {
                "user_id": user_id,
                "name": data.get("name", ""),
                "email": data.get("email", ""),
                "phone": data.get("phone", ""),
                "tier": data.get("tier", "regular"),
                "preferences": data.get("preferences", {}),
                "created_at": datetime.now().isoformat(),
                "last_interaction": datetime.now().isoformat(),
                "total_spent": 0.0,
                "visit_count": 0
            }
        else:
            # Update existing customer
            customer = self.customers[user_id]
            for key, value in data.items():
                if key != "user_id":  # Don't allow changing user_id
                    customer[key] = value
            customer["last_interaction"] = datetime.now().isoformat()
        
        return self.customers[user_id]

    def get_order_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get customer order history"""
        orders = self.orders.get(user_id, [])
        return sorted(orders, key=lambda x: x["date"], reverse=True)[:limit]

    def create_support_ticket(self, user_id: str, subject: str, description: str, priority: str = "normal") -> Dict:
        """Create a support ticket"""
        ticket_id = str(uuid.uuid4())
        
        ticket = {
            "id": ticket_id,
            "user_id": user_id,
            "subject": subject,
            "description": description,
            "status": "open",
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "assigned_to": None,
            "resolution": None
        }
        
        if user_id not in self.support_tickets:
            self.support_tickets[user_id] = []
        
        self.support_tickets[user_id].append(ticket)
        return ticket

    def update_ticket_status(self, ticket_id: str, status: str, notes: str = "") -> Dict:
        """Update ticket status"""
        for user_id, tickets in self.support_tickets.items():
            for ticket in tickets:
                if ticket["id"] == ticket_id:
                    ticket["status"] = status
                    ticket["updated_at"] = datetime.now().isoformat()
                    if notes:
                        ticket["resolution"] = notes
                    return ticket
        
        raise ValueError("Ticket not found")

    def get_user_tickets(self, user_id: str, status: str = None) -> List[Dict]:
        """Get user support tickets"""
        tickets = self.support_tickets.get(user_id, [])
        
        if status:
            tickets = [t for t in tickets if t["status"] == status]
        
        return sorted(tickets, key=lambda x: x["created_at"], reverse=True)

    def log_interaction(self, user_id: str, interaction_type: str, details: Dict) -> Dict:
        """Log customer interaction"""
        interaction = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": interaction_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        if user_id not in self.interactions:
            self.interactions[user_id] = []
        
        self.interactions[user_id].append(interaction)
        
        # Update customer last interaction
        if user_id in self.customers:
            self.customers[user_id]["last_interaction"] = datetime.now().isoformat()
        
        return interaction

    def get_customer_insights(self, user_id: str) -> Dict:
        """Get customer insights and analytics"""
        customer = self.get_customer_profile(user_id)
        if not customer:
            return {"error": "Customer not found"}
        
        orders = self.get_order_history(user_id)
        tickets = self.get_user_tickets(user_id)
        interactions = self.interactions.get(user_id, [])
        
        # Calculate insights
        total_orders = len(orders)
        avg_order_value = customer.get("total_spent", 0) / max(total_orders, 1)
        open_tickets = len([t for t in tickets if t["status"] == "open"])
        last_order_date = orders[0]["date"] if orders else None
        
        # Determine customer health score (0-100)
        health_score = 100
        if open_tickets > 0:
            health_score -= open_tickets * 10
        if last_order_date:
            days_since_last_order = (datetime.now() - datetime.fromisoformat(last_order_date)).days
            if days_since_last_order > 90:
                health_score -= 20
        
        health_score = max(0, min(100, health_score))
        
        return {
            "customer_id": user_id,
            "tier": customer.get("tier", "regular"),
            "total_orders": total_orders,
            "total_spent": customer.get("total_spent", 0),
            "avg_order_value": avg_order_value,
            "visit_count": customer.get("visit_count", 0),
            "open_tickets": open_tickets,
            "health_score": health_score,
            "last_order_date": last_order_date,
            "preferred_services": customer.get("preferences", {}).get("favorite_service"),
            "communication_preference": "email" if customer.get("email") else "phone",
            "loyalty_status": self._calculate_loyalty_status(customer),
            "risk_factors": self._identify_risk_factors(customer, orders, tickets)
        }

    def _calculate_loyalty_status(self, customer: Dict) -> str:
        """Calculate customer loyalty status"""
        visit_count = customer.get("visit_count", 0)
        total_spent = customer.get("total_spent", 0)
        
        if visit_count >= 10 and total_spent >= 500:
            return "champion"
        elif visit_count >= 5 and total_spent >= 200:
            return "loyal"
        elif visit_count >= 2:
            return "regular"
        else:
            return "new"

    def _identify_risk_factors(self, customer: Dict, orders: List[Dict], tickets: List[Dict]) -> List[str]:
        """Identify customer risk factors"""
        risk_factors = []
        
        # Check for long time since last interaction
        if customer.get("last_interaction"):
            days_since_interaction = (datetime.now() - datetime.fromisoformat(customer["last_interaction"])).days
            if days_since_interaction > 60:
                risk_factors.append("long_absence")
        
        # Check for frequent support tickets
        recent_tickets = [t for t in tickets if (datetime.now() - datetime.fromisoformat(t["created_at"])).days <= 30]
        if len(recent_tickets) > 2:
            risk_factors.append("frequent_complaints")
        
        # Check for declined orders (would be in a real system)
        # For demo, randomly assign some risk factors
        if random.random() < 0.1:
            risk_factors.append("payment_issues")
        
        return risk_factors


# Global mock CRM database
mock_crm = MockCRMDatabase()


class GetCustomerProfileTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_customer_profile",
            description="Buscar perfil completo do cliente"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="user_id",
                    type="string",
                    description="ID do usuário",
                    required=True
                )
            ],
            category="crm",
            timeout=10
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            profile = mock_crm.get_customer_profile(parameters["user_id"])
            
            if not profile:
                return {
                    "success": False,
                    "error": "Customer not found",
                    "message": "Cliente não encontrado no sistema"
                }
            
            return {
                "success": True,
                "profile": profile,
                "message": f"Perfil encontrado: {profile.get('name', 'N/A')}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao buscar perfil: {str(e)}"
            }


class UpdateCustomerInfoTool(Tool):
    def __init__(self):
        super().__init__(
            name="update_customer_info",
            description="Atualizar informações do cliente"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="user_id",
                    type="string",
                    description="ID do usuário",
                    required=True
                ),
                ToolParameter(
                    name="data",
                    type="object",
                    description="Dados para atualizar",
                    required=True
                )
            ],
            category="crm",
            timeout=15
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            updated_profile = mock_crm.update_customer_info(
                parameters["user_id"],
                parameters["data"]
            )
            
            return {
                "success": True,
                "profile": updated_profile,
                "message": "Informações atualizadas com sucesso"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao atualizar informações: {str(e)}"
            }


class GetOrderHistoryTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_order_history",
            description="Buscar histórico de pedidos do cliente"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="user_id",
                    type="string",
                    description="ID do usuário",
                    required=True
                ),
                ToolParameter(
                    name="limit",
                    type="integer",
                    description="Número máximo de pedidos a retornar",
                    required=False
                )
            ],
            category="crm",
            timeout=10
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            orders = mock_crm.get_order_history(
                parameters["user_id"],
                parameters.get("limit", 10)
            )
            
            return {
                "success": True,
                "orders": orders,
                "total": len(orders),
                "message": f"Encontrados {len(orders)} pedidos"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao buscar histórico: {str(e)}"
            }


class CreateSupportTicketTool(Tool):
    def __init__(self):
        super().__init__(
            name="create_support_ticket",
            description="Criar ticket de suporte"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="user_id",
                    type="string",
                    description="ID do usuário",
                    required=True
                ),
                ToolParameter(
                    name="subject",
                    type="string",
                    description="Assunto do ticket",
                    required=True
                ),
                ToolParameter(
                    name="description",
                    type="string",
                    description="Descrição detalhada do problema",
                    required=True
                ),
                ToolParameter(
                    name="priority",
                    type="string",
                    description="Prioridade do ticket",
                    required=False,
                    enum=["low", "normal", "high", "urgent"]
                )
            ],
            category="crm",
            timeout=15
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ticket = mock_crm.create_support_ticket(
                user_id=parameters["user_id"],
                subject=parameters["subject"],
                description=parameters["description"],
                priority=parameters.get("priority", "normal")
            )
            
            return {
                "success": True,
                "ticket": ticket,
                "message": f"Ticket #{ticket['id'][:8]} criado com sucesso"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao criar ticket: {str(e)}"
            }


class GetUserTicketsTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_user_tickets",
            description="Buscar tickets de suporte do usuário"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="user_id",
                    type="string",
                    description="ID do usuário",
                    required=True
                ),
                ToolParameter(
                    name="status",
                    type="string",
                    description="Filtrar por status",
                    required=False,
                    enum=["open", "in_progress", "closed"]
                )
            ],
            category="crm",
            timeout=10
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            tickets = mock_crm.get_user_tickets(
                parameters["user_id"],
                parameters.get("status")
            )
            
            return {
                "success": True,
                "tickets": tickets,
                "total": len(tickets),
                "message": f"Encontrados {len(tickets)} tickets"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao buscar tickets: {str(e)}"
            }


class GetCustomerInsightsTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_customer_insights",
            description="Obter insights e análises do cliente"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="user_id",
                    type="string",
                    description="ID do usuário",
                    required=True
                )
            ],
            category="crm",
            timeout=15
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            insights = mock_crm.get_customer_insights(parameters["user_id"])
            
            if "error" in insights:
                return {
                    "success": False,
                    "error": insights["error"],
                    "message": "Cliente não encontrado"
                }
            
            return {
                "success": True,
                "insights": insights,
                "message": f"Insights gerados - Score: {insights['health_score']}/100"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao gerar insights: {str(e)}"
            }


class LogInteractionTool(Tool):
    def __init__(self):
        super().__init__(
            name="log_interaction",
            description="Registrar interação com o cliente"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="user_id",
                    type="string",
                    description="ID do usuário",
                    required=True
                ),
                ToolParameter(
                    name="interaction_type",
                    type="string",
                    description="Tipo de interação",
                    required=True,
                    enum=["chat", "call", "email", "visit", "complaint", "compliment"]
                ),
                ToolParameter(
                    name="details",
                    type="object",
                    description="Detalhes da interação",
                    required=True
                )
            ],
            category="crm",
            timeout=10
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            interaction = mock_crm.log_interaction(
                user_id=parameters["user_id"],
                interaction_type=parameters["interaction_type"],
                details=parameters["details"]
            )
            
            return {
                "success": True,
                "interaction": interaction,
                "message": "Interação registrada com sucesso"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao registrar interação: {str(e)}"
            }


# Register all CRM tools
def register_crm_tools():
    from ..core.tools import register_tool
    
    register_tool(GetCustomerProfileTool(), "crm")
    register_tool(UpdateCustomerInfoTool(), "crm")
    register_tool(GetOrderHistoryTool(), "crm")
    register_tool(CreateSupportTicketTool(), "crm")
    register_tool(GetUserTicketsTool(), "crm")
    register_tool(GetCustomerInsightsTool(), "crm")
    register_tool(LogInteractionTool(), "crm")