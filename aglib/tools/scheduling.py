from __future__ import annotations
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.tools import Tool
from ..core.types import ToolDefinition, ToolParameter


# Mock database for development
class MockSchedulingDB:
    def __init__(self):
        self.appointments: Dict[str, Dict] = {}
        self.availability: Dict[str, List[str]] = self._generate_mock_availability()
        self.services = {
            "corte_masculino": {"duration": 30, "price": 45.00, "name": "Corte Masculino"},
            "corte_feminino": {"duration": 60, "price": 65.00, "name": "Corte Feminino"},
            "barba": {"duration": 20, "price": 25.00, "name": "Barba"},
            "sobrancelha": {"duration": 15, "price": 20.00, "name": "Sobrancelha"},
            "coloracao": {"duration": 120, "price": 120.00, "name": "Coloração"},
            "escova": {"duration": 45, "price": 35.00, "name": "Escova"},
        }

    def _generate_mock_availability(self) -> Dict[str, List[str]]:
        """Generate mock availability for next 30 days"""
        availability = {}
        base_date = datetime.now().date()
        
        for i in range(30):
            date_str = (base_date + timedelta(days=i)).isoformat()
            # Skip Sundays (weekday 6)
            current_date = base_date + timedelta(days=i)
            if current_date.weekday() == 6:
                availability[date_str] = []
                continue
            
            # Generate time slots from 9:00 to 18:00
            time_slots = []
            for hour in range(9, 18):
                for minute in [0, 30]:
                    time_slots.append(f"{hour:02d}:{minute:02d}")
            
            availability[date_str] = time_slots
        
        return availability

    def is_slot_available(self, date: str, time: str, duration: int = 30) -> bool:
        """Check if a time slot is available"""
        if date not in self.availability:
            return False
        
        # Check if the requested time slot exists
        if time not in self.availability[date]:
            return False
        
        # Check if slot is already booked
        for appointment in self.appointments.values():
            if (appointment["date"] == date and 
                appointment["time"] == time and 
                appointment["status"] != "cancelled"):
                return False
        
        return True

    def book_appointment(self, user_id: str, date: str, time: str, service: str, notes: str = "") -> Dict:
        """Book an appointment"""
        appointment_id = str(uuid.uuid4())
        
        if service not in self.services:
            raise ValueError(f"Service '{service}' not available")
        
        if not self.is_slot_available(date, time):
            raise ValueError(f"Time slot {date} {time} is not available")
        
        appointment = {
            "id": appointment_id,
            "user_id": user_id,
            "date": date,
            "time": time,
            "service": service,
            "service_info": self.services[service],
            "notes": notes,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.appointments[appointment_id] = appointment
        return appointment

    def cancel_appointment(self, appointment_id: str) -> Dict:
        """Cancel an appointment"""
        if appointment_id not in self.appointments:
            raise ValueError("Appointment not found")
        
        appointment = self.appointments[appointment_id]
        appointment["status"] = "cancelled"
        appointment["updated_at"] = datetime.now().isoformat()
        
        return appointment

    def reschedule_appointment(self, appointment_id: str, new_date: str, new_time: str) -> Dict:
        """Reschedule an appointment"""
        if appointment_id not in self.appointments:
            raise ValueError("Appointment not found")
        
        appointment = self.appointments[appointment_id]
        
        if not self.is_slot_available(new_date, new_time):
            raise ValueError(f"New time slot {new_date} {new_time} is not available")
        
        appointment["date"] = new_date
        appointment["time"] = new_time
        appointment["updated_at"] = datetime.now().isoformat()
        
        return appointment

    def get_user_appointments(self, user_id: str, date_from: str = None) -> List[Dict]:
        """Get user appointments"""
        user_appointments = []
        
        for appointment in self.appointments.values():
            if appointment["user_id"] == user_id and appointment["status"] != "cancelled":
                if date_from is None or appointment["date"] >= date_from:
                    user_appointments.append(appointment)
        
        return sorted(user_appointments, key=lambda x: (x["date"], x["time"]))

    def get_available_slots(self, date: str, service: str = None) -> List[str]:
        """Get available time slots for a date"""
        if date not in self.availability:
            return []
        
        available_slots = []
        duration = 30  # default duration
        
        if service and service in self.services:
            duration = self.services[service]["duration"]
        
        for time_slot in self.availability[date]:
            if self.is_slot_available(date, time_slot, duration):
                available_slots.append(time_slot)
        
        return available_slots


# Global mock database instance
mock_db = MockSchedulingDB()


class CheckAvailabilityTool(Tool):
    def __init__(self):
        super().__init__(
            name="check_availability",
            description="Verificar disponibilidade de horários para agendamento"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="date",
                    type="string",
                    description="Data para verificar disponibilidade (formato YYYY-MM-DD)",
                    required=True,
                    format="date"
                ),
                ToolParameter(
                    name="service",
                    type="string",
                    description="Tipo de serviço (opcional, ajuda a verificar duração)",
                    required=False,
                    enum=list(mock_db.services.keys())
                )
            ],
            category="scheduling",
            timeout=10
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        date = parameters["date"]
        service = parameters.get("service")
        
        try:
            available_slots = mock_db.get_available_slots(date, service)
            service_info = mock_db.services.get(service, {}) if service else {}
            
            return {
                "date": date,
                "available_slots": available_slots,
                "total_slots": len(available_slots),
                "service": service,
                "service_info": service_info
            }
        except Exception as e:
            raise Exception(f"Erro ao verificar disponibilidade: {str(e)}")


class BookAppointmentTool(Tool):
    def __init__(self):
        super().__init__(
            name="book_appointment",
            description="Agendar um compromisso"
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
                    name="date",
                    type="string",
                    description="Data do agendamento (formato YYYY-MM-DD)",
                    required=True,
                    format="date"
                ),
                ToolParameter(
                    name="time",
                    type="string",
                    description="Horário do agendamento (formato HH:MM)",
                    required=True
                ),
                ToolParameter(
                    name="service",
                    type="string",
                    description="Tipo de serviço",
                    required=True,
                    enum=list(mock_db.services.keys())
                ),
                ToolParameter(
                    name="notes",
                    type="string",
                    description="Observações adicionais",
                    required=False
                )
            ],
            category="scheduling",
            timeout=15
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            appointment = mock_db.book_appointment(
                user_id=parameters["user_id"],
                date=parameters["date"],
                time=parameters["time"],
                service=parameters["service"],
                notes=parameters.get("notes", "")
            )
            
            return {
                "success": True,
                "appointment": appointment,
                "message": f"Agendamento criado com sucesso para {appointment['date']} às {appointment['time']}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao criar agendamento: {str(e)}"
            }


class CancelAppointmentTool(Tool):
    def __init__(self):
        super().__init__(
            name="cancel_appointment",
            description="Cancelar um agendamento"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="appointment_id",
                    type="string",
                    description="ID do agendamento a ser cancelado",
                    required=True
                ),
                ToolParameter(
                    name="reason",
                    type="string",
                    description="Motivo do cancelamento",
                    required=False
                )
            ],
            category="scheduling",
            timeout=10
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            appointment = mock_db.cancel_appointment(parameters["appointment_id"])
            
            return {
                "success": True,
                "appointment": appointment,
                "message": f"Agendamento cancelado com sucesso"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao cancelar agendamento: {str(e)}"
            }


class RescheduleAppointmentTool(Tool):
    def __init__(self):
        super().__init__(
            name="reschedule_appointment",
            description="Reagendar um compromisso"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="appointment_id",
                    type="string",
                    description="ID do agendamento a ser reagendado",
                    required=True
                ),
                ToolParameter(
                    name="new_date",
                    type="string",
                    description="Nova data (formato YYYY-MM-DD)",
                    required=True,
                    format="date"
                ),
                ToolParameter(
                    name="new_time",
                    type="string",
                    description="Novo horário (formato HH:MM)",
                    required=True
                )
            ],
            category="scheduling",
            timeout=15
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            appointment = mock_db.reschedule_appointment(
                appointment_id=parameters["appointment_id"],
                new_date=parameters["new_date"],
                new_time=parameters["new_time"]
            )
            
            return {
                "success": True,
                "appointment": appointment,
                "message": f"Agendamento reagendado para {appointment['date']} às {appointment['time']}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao reagendar: {str(e)}"
            }


class GetUserAppointmentsTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_user_appointments",
            description="Buscar agendamentos do usuário"
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
                    name="date_from",
                    type="string",
                    description="Data a partir da qual buscar (formato YYYY-MM-DD)",
                    required=False,
                    format="date"
                )
            ],
            category="scheduling",
            timeout=10
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        try:
            appointments = mock_db.get_user_appointments(
                user_id=parameters["user_id"],
                date_from=parameters.get("date_from")
            )
            
            return {
                "success": True,
                "appointments": appointments,
                "total": len(appointments),
                "message": f"Encontrados {len(appointments)} agendamentos"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erro ao buscar agendamentos: {str(e)}"
            }


class ListServicesTool(Tool):
    def __init__(self):
        super().__init__(
            name="list_services",
            description="Listar serviços disponíveis"
        )

    def _create_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=[],
            category="scheduling",
            timeout=5
        )

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "services": mock_db.services,
            "total": len(mock_db.services),
            "message": f"Temos {len(mock_db.services)} serviços disponíveis"
        }


# Register all scheduling tools
def register_scheduling_tools():
    from ..core.tools import register_tool
    
    register_tool(CheckAvailabilityTool(), "scheduling")
    register_tool(BookAppointmentTool(), "scheduling")
    register_tool(CancelAppointmentTool(), "scheduling")
    register_tool(RescheduleAppointmentTool(), "scheduling")
    register_tool(GetUserAppointmentsTool(), "scheduling")
    register_tool(ListServicesTool(), "scheduling")