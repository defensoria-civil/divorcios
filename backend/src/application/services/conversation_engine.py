from typing import Optional
from sqlalchemy.orm import Session
from opentelemetry import trace

from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.repositories import CaseRepository, MessageRepository
from infrastructure.validation.response_validation_service_impl import SimpleResponseValidationService
from infrastructure.validation.address_validation_service_impl import SimpleAddressValidationService
from infrastructure.validation.date_validation_service_impl import SimpleDateValidationService
from infrastructure.services.user_recognition_service_impl import SimpleUserRecognitionService
from infrastructure.ai.router import LLMRouter
from infrastructure.ai.safety_layer import SafetyLayer

tracer = trace.get_tracer(__name__)


class ConversationEngine:
    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()
        self.cases = CaseRepository(self.db)
        self.messages = MessageRepository(self.db)
        self.validator_resp = SimpleResponseValidationService()
        self.validator_addr = SimpleAddressValidationService()
        self.validator_date = SimpleDateValidationService()
        self.user_recog = SimpleUserRecognitionService()
        self.llm = LLMRouter()
        self.safety = SafetyLayer()

    async def handle_incoming(self, phone: str, text: str) -> str:
        with tracer.start_as_current_span("conversation.handle_incoming") as span:
            span.set_attribute("conversation.phone", phone)

            safety_result = self.safety.filter_input(text)
            if not safety_result.allowed:
                span.set_attribute("conversation.blocked_reason", safety_result.reason or "prompt_injection")
                reply = (
                    "No puedo procesar esa solicitud. Por favor reformulá tu mensaje "
                    "sin instrucciones técnicas hacia el sistema."
                )
                # Creamos un caso si no existe, para mantener el historial consistente
                case = self.cases.get_or_create_by_phone(phone)
                self.messages.add_message(case.id, "user", text)
                self.messages.add_message(case.id, "assistant", reply)
                return reply

            case = self.cases.get_or_create_by_phone(phone)
            span.set_attribute("conversation.case_id", getattr(case, "id", None))
            span.set_attribute("conversation.phase", getattr(case, "phase", None))

            self.messages.add_message(case.id, "user", text)

        # Simple finite-state flow
        if case.phase == "inicio":
            case.phase = "tipo_divorcio"
            self.cases.update(case)
            reply = (
                "¡Hola! Soy tu asistente de la Defensoría Civil de San Rafael.\n"
                "¿Qué tipo de divorcio querés iniciar: unilateral (solo vos) o conjunta (los dos)?"
            )
            self.messages.add_message(case.id, "assistant", reply)
            return reply

        if case.phase == "tipo_divorcio":
            low = text.lower()
            if "unilateral" in low or "conjunta" in low:
                case.type = "unilateral" if "unilateral" in low else "conjunta"
                case.phase = "nombre"
                self.cases.update(case)
                reply = "Perfecto. Ahora necesito algunos datos personales. ¿Cuál es tu nombre completo?"
                self.messages.add_message(case.id, "assistant", reply)
                return reply
            else:
                reply = "Por favor respondé 'unilateral' o 'conjunta'."
                self.messages.add_message(case.id, "assistant", reply)
                return reply

        if case.phase == "nombre":
            r = self.validator_resp.validate_user_response(text, "nombre", "nombre completo")
            if not r.is_valid:
                reply = "Necesito tu nombre completo real para continuar."
                self.messages.add_message(case.id, "assistant", reply)
                return reply
            case.nombre = text.strip()
            case.phase = "dni"
            self.cases.update(case)
            reply = "Gracias. ¿Cuál es tu número de DNI?"
            self.messages.add_message(case.id, "assistant", reply)
            return reply

        if case.phase == "dni":
            r = self.validator_resp.validate_user_response(text, "dni", "documento")
            if not r.is_valid:
                reply = "Ingresá un DNI válido de 7 u 8 dígitos."
                self.messages.add_message(case.id, "assistant", reply)
                return reply
            case.dni = text.strip()
            case.phase = "fecha_nacimiento"
            self.cases.update(case)
            reply = "¿Cuál es tu fecha de nacimiento? (DD/MM/AAAA)"
            self.messages.add_message(case.id, "assistant", reply)
            return reply

        if case.phase == "fecha_nacimiento":
            res = self.validator_date.validate_birth_date(text)
            if not res.is_valid:
                reply = "Fecha inválida. Formato DD/MM/AAAA y debés ser mayor de 18 años."
                self.messages.add_message(case.id, "assistant", reply)
                return reply
            case.fecha_nacimiento = None  # almacenar vía parse si se requiere
            case.phase = "domicilio"
            self.cases.update(case)
            reply = "¿Cuál es tu domicilio actual? (ej: San Martín 123, San Rafael, Mendoza)"
            self.messages.add_message(case.id, "assistant", reply)
            return reply

        if case.phase == "domicilio":
            res = self.validator_addr.validate_address(text)
            if not res.is_valid:
                reply = "Dirección incompleta. Indicá calle y número, ciudad y provincia."
                self.messages.add_message(case.id, "assistant", reply)
                return reply
            case.domicilio = res.normalized_address or text.strip()
            case.phase = "documentacion"
            self.cases.update(case)
            reply = (
                "✅ Datos personales cargados. Fase 2: Documentación. Podés enviar DNI y acta de matrimonio en PDF/JPG."
            )
            self.messages.add_message(case.id, "assistant", reply)
            return reply

        # Fallback to LLM for general questions during documentation phase
        history = [
            {"role": m.role, "content": m.content}
            for m in reversed(self.messages.last_messages(case.id, limit=10))
        ]
        answer = await self.llm.chat(history + [{"role": "user", "content": text}])
        self.messages.add_message(case.id, "assistant", answer)
        return answer
