from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List
import random

from ..core.tools import Tool
from ..core.types import ToolDefinition, ToolParameter


# Mock payment gateway for development
class MockPaymentGateway:
    def __init__(self):
        self.transactions: Dict[str, Dict] = {}
        self.payment_methods: Dict[str, List[Dict]] = {}
        self.invoices: Dict[str, Dict] = {}

        # Payment method types
        self.method_types = {
            "credit_card": "Cartão de Crédito",
            "debit_card": "Cartão de Débito",
            "pix": "PIX",
            "cash": "Dinheiro",
            "bank_transfer": "Transferência Bancária",
        }

    def add_payment_method(self, user_id: str, method_data: Dict) -> Dict:
        """Add a payment method for user"""
        if user_id not in self.payment_methods:
            self.payment_methods[user_id] = []

        method_id = str(uuid.uuid4())
        payment_method = {
            "id": method_id,
            "type": method_data["type"],
            "display_name": method_data.get("display_name", ""),
            "is_default": method_data.get("is_default", False),
            "created_at": datetime.now().isoformat(),
            # For demo purposes, don't store sensitive data
            "masked_info": self._mask_sensitive_data(method_data),
        }

        self.payment_methods[user_id].append(payment_method)
        return payment_method

    def _mask_sensitive_data(self, method_data: Dict) -> str:
        """Mask sensitive payment data for display"""
        method_type = method_data["type"]

        if method_type in ["credit_card", "debit_card"]:
            card_number = method_data.get("card_number", "")
            if len(card_number) >= 4:
                return f"****-****-****-{card_number[-4:]}"
        elif method_type == "pix":
            pix_key = method_data.get("pix_key", "")
            if "@" in pix_key:  # email
                parts = pix_key.split("@")
                return f"{parts[0][:2]}***@{parts[1]}"
            elif len(pix_key) > 4:
                return f"{pix_key[:2]}***{pix_key[-2:]}"

        return "***"

    def process_payment(
        self, amount: float, currency: str, method_id: str, order_id: str
    ) -> Dict:
        """Process a payment"""
        transaction_id = str(uuid.uuid4())

        # Simulate payment processing
        success_rate = 0.95  # 95% success rate for demo
        is_successful = random.random() < success_rate

        if not is_successful:
            # Simulate different failure reasons
            failure_reasons = [
                "Cartão recusado",
                "Saldo insuficiente",
                "Erro na operadora",
                "Dados inválidos",
            ]

            transaction = {
                "id": transaction_id,
                "amount": amount,
                "currency": currency,
                "method_id": method_id,
                "order_id": order_id,
                "status": "failed",
                "failure_reason": random.choice(failure_reasons),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
        else:
            transaction = {
                "id": transaction_id,
                "amount": amount,
                "currency": currency,
                "method_id": method_id,
                "order_id": order_id,
                "status": "completed",
                "authorization_code": f"AUTH{random.randint(100000, 999999)}",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

        self.transactions[transaction_id] = transaction
        return transaction

    def check_payment_status(self, transaction_id: str) -> Dict:
        """Check payment status"""
        if transaction_id not in self.transactions:
            raise ValueError("Transaction not found")

        return self.transactions[transaction_id]

    def refund_payment(self, transaction_id: str, amount: float, reason: str) -> Dict:
        """Process a refund"""
        if transaction_id not in self.transactions:
            raise ValueError("Transaction not found")

        original_transaction = self.transactions[transaction_id]

        if original_transaction["status"] != "completed":
            raise ValueError("Can only refund completed transactions")

        if amount > original_transaction["amount"]:
            raise ValueError("Refund amount cannot exceed original amount")

        refund_id = str(uuid.uuid4())
        refund = {
            "id": refund_id,
            "original_transaction_id": transaction_id,
            "amount": amount,
            "reason": reason,
            "status": "completed",
            "created_at": datetime.now().isoformat(),
        }

        # Update original transaction
        original_transaction["refunded_amount"] = (
            original_transaction.get("refunded_amount", 0) + amount
        )
        original_transaction["updated_at"] = datetime.now().isoformat()

        self.transactions[refund_id] = refund
        return refund

    def generate_invoice(self, order_id: str, items: List[Dict]) -> Dict:
        """Generate an invoice"""
        invoice_id = str(uuid.uuid4())

        total_amount = sum(item["price"] * item["quantity"] for item in items)

        invoice = {
            "id": invoice_id,
            "order_id": order_id,
            "items": items,
            "subtotal": total_amount,
            "tax_amount": total_amount * 0.0,  # No tax for demo
            "total_amount": total_amount,
            "currency": "BRL",
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }

        self.invoices[invoice_id] = invoice
        return invoice

    def get_transaction_history(
        self, user_id: str, date_from: str = None, date_to: str = None
    ) -> List[Dict]:
        """Get transaction history for user"""
        # In a real system, you'd filter by user_id properly
        # For demo, return all transactions
        transactions = list(self.transactions.values())

        if date_from:
            transactions = [t for t in transactions if t["created_at"] >= date_from]

        if date_to:
            transactions = [t for t in transactions if t["created_at"] <= date_to]

        return sorted(transactions, key=lambda x: x["created_at"], reverse=True)


# Global mock payment gateway
mock_gateway = MockPaymentGateway()


class GetPaymentMethodsTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_payment_methods",
            description="Listar métodos de pagamento do usuário",
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
                    required=True,
                )
            ],
            category="payments",
            timeout=10,
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        user_id = parameters["user_id"]

        try:
            methods = mock_gateway.payment_methods.get(user_id, [])

            return {
                "success": True,
                "payment_methods": methods,
                "total": len(methods),
                "available_types": mock_gateway.method_types,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao buscar métodos de pagamento: {str(e)}",
            }


class AddPaymentMethodTool(Tool):
    def __init__(self):
        super().__init__(
            name="add_payment_method", description="Adicionar método de pagamento"
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
                    required=True,
                ),
                ToolParameter(
                    name="method_type",
                    type="string",
                    description="Tipo de método de pagamento",
                    required=True,
                    enum=list(mock_gateway.method_types.keys()),
                ),
                ToolParameter(
                    name="display_name",
                    type="string",
                    description="Nome para exibição",
                    required=False,
                ),
                ToolParameter(
                    name="is_default",
                    type="boolean",
                    description="Definir como método padrão",
                    required=False,
                ),
            ],
            category="payments",
            timeout=15,
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            method_data = {
                "type": parameters["method_type"],
                "display_name": parameters.get("display_name", ""),
                "is_default": parameters.get("is_default", False),
            }

            payment_method = mock_gateway.add_payment_method(
                parameters["user_id"], method_data
            )

            return {
                "success": True,
                "payment_method": payment_method,
                "message": "Método de pagamento adicionado com sucesso",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao adicionar método de pagamento: {str(e)}",
            }


class ProcessPaymentTool(Tool):
    def __init__(self):
        super().__init__(name="process_payment", description="Processar um pagamento")

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="amount",
                    type="number",
                    description="Valor do pagamento",
                    required=True,
                ),
                ToolParameter(
                    name="currency",
                    type="string",
                    description="Moeda",
                    required=False,
                    enum=["BRL", "USD", "EUR"],
                ),
                ToolParameter(
                    name="method_id",
                    type="string",
                    description="ID do método de pagamento",
                    required=True,
                ),
                ToolParameter(
                    name="order_id",
                    type="string",
                    description="ID do pedido",
                    required=True,
                ),
            ],
            category="payments",
            requires_auth=True,
            timeout=30,
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            transaction = mock_gateway.process_payment(
                amount=parameters["amount"],
                currency=parameters.get("currency", "BRL"),
                method_id=parameters["method_id"],
                order_id=parameters["order_id"],
            )

            if transaction["status"] == "completed":
                return {
                    "success": True,
                    "transaction": transaction,
                    "message": f"Pagamento de R$ {parameters['amount']:.2f} processado com sucesso",
                }
            else:
                return {
                    "success": False,
                    "transaction": transaction,
                    "error": transaction.get("failure_reason", "Erro desconhecido"),
                    "message": f"Falha no pagamento: {transaction.get('failure_reason', 'Erro desconhecido')}",
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao processar pagamento: {str(e)}",
            }


class CheckPaymentStatusTool(Tool):
    def __init__(self):
        super().__init__(
            name="check_payment_status", description="Verificar status de um pagamento"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="transaction_id",
                    type="string",
                    description="ID da transação",
                    required=True,
                )
            ],
            category="payments",
            timeout=10,
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            transaction = mock_gateway.check_payment_status(
                parameters["transaction_id"]
            )

            return {
                "success": True,
                "transaction": transaction,
                "status": transaction["status"],
                "message": f"Status do pagamento: {transaction['status']}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao verificar status: {str(e)}",
            }


class GenerateInvoiceTool(Tool):
    def __init__(self):
        super().__init__(name="generate_invoice", description="Gerar uma fatura")

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="order_id",
                    type="string",
                    description="ID do pedido",
                    required=True,
                ),
                ToolParameter(
                    name="items",
                    type="array",
                    description="Lista de itens da fatura",
                    required=True,
                ),
            ],
            category="payments",
            timeout=15,
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            invoice = mock_gateway.generate_invoice(
                order_id=parameters["order_id"], items=parameters["items"]
            )

            return {
                "success": True,
                "invoice": invoice,
                "invoice_url": f"https://example.com/invoices/{invoice['id']}.pdf",
                "message": "Fatura gerada com sucesso",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao gerar fatura: {str(e)}",
            }


class RefundPaymentTool(Tool):
    def __init__(self):
        super().__init__(
            name="refund_payment", description="Processar estorno de pagamento"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="transaction_id",
                    type="string",
                    description="ID da transação original",
                    required=True,
                ),
                ToolParameter(
                    name="amount",
                    type="number",
                    description="Valor do estorno",
                    required=True,
                ),
                ToolParameter(
                    name="reason",
                    type="string",
                    description="Motivo do estorno",
                    required=True,
                ),
            ],
            category="payments",
            requires_auth=True,
            timeout=30,
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            refund = mock_gateway.refund_payment(
                transaction_id=parameters["transaction_id"],
                amount=parameters["amount"],
                reason=parameters["reason"],
            )

            return {
                "success": True,
                "refund": refund,
                "message": f"Estorno de R$ {parameters['amount']:.2f} processado com sucesso",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao processar estorno: {str(e)}",
            }


class GetTransactionHistoryTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_transaction_history", description="Buscar histórico de transações"
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
                    required=True,
                ),
                ToolParameter(
                    name="date_from",
                    type="string",
                    description="Data inicial (formato YYYY-MM-DD)",
                    required=False,
                    format="date",
                ),
                ToolParameter(
                    name="date_to",
                    type="string",
                    description="Data final (formato YYYY-MM-DD)",
                    required=False,
                    format="date",
                ),
            ],
            category="payments",
            timeout=15,
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            transactions = mock_gateway.get_transaction_history(
                user_id=parameters["user_id"],
                date_from=parameters.get("date_from"),
                date_to=parameters.get("date_to"),
            )

            return {
                "success": True,
                "transactions": transactions,
                "total": len(transactions),
                "message": f"Encontradas {len(transactions)} transações",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao buscar histórico: {str(e)}",
            }


# Register all payment tools
def register_payment_tools():
    from ..core.tools import register_tool

    register_tool(GetPaymentMethodsTool(), "payments")
    register_tool(AddPaymentMethodTool(), "payments")
    register_tool(ProcessPaymentTool(), "payments")
    register_tool(CheckPaymentStatusTool(), "payments")
    register_tool(GenerateInvoiceTool(), "payments")
    register_tool(RefundPaymentTool(), "payments")
    register_tool(GetTransactionHistoryTool(), "payments")
