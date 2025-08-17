from typing import Optional
from ..core.types import Message

class HandoffPolicy:
    def select_specialist(self, msg: Message) -> Optional[str]:
        t = msg.text.lower()
        if "pagamento" in t or "pagar" in t:
            return "Specialist:Payments"
        if "agenda" in t or "agendar" in t or "marcar" in t:
            return "Specialist:Scheduling"
        return None
