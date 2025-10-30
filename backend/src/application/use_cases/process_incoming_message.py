from typing import Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
import structlog

from infrastructure.persistence.repositories import CaseRepository, MessageRepository
from infrastructure.ai.router import LLMRouter
from infrastructure.validation.response_validation_service_impl import SimpleResponseValidationService
from infrastructure.validation.address_validation_service_impl import SimpleAddressValidationService
from infrastructure.validation.date_validation_service_impl import SimpleDateValidationService
from application.services.memory_service import MemoryService
from application.services.hallucination_detection_service import HallucinationDetectionService

logger = structlog.get_logger()

@dataclass
class IncomingMessageRequest:
    """DTO para mensaje entrante"""
    phone: str
    text: str
    media_id: Optional[str] = None

@dataclass
class MessageResponse:
    """DTO para respuesta"""
    text: str
    send_document: bool = False
    document_path: Optional[str] = None

class ProcessIncomingMessageUseCase:
    """
    Caso de uso principal: Procesar mensaje entrante de WhatsApp
    Orquesta validación, memoria contextual, LLM y flujo de estados
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.cases = CaseRepository(db)
        self.messages = MessageRepository(db)
        self.llm = LLMRouter()
        self.memory = MemoryService(db, self.llm)
        self.hallucination = HallucinationDetectionService()
        self.validator_resp = SimpleResponseValidationService()
        self.validator_addr = SimpleAddressValidationService()
        self.validator_date = SimpleDateValidationService()
    
    async def execute(self, request: IncomingMessageRequest) -> MessageResponse:
        """Ejecuta el caso de uso"""
        phone = request.phone
        text = request.text
        
        # 1. Obtener o crear caso
        case = self.cases.get_or_create_by_phone(phone)
        
        # 2. Almacenar mensaje del usuario en DB y memoria
        self.messages.add_message(case.id, "user", text)
        await self.memory.store_immediate_memory(case.id, f"Usuario: {text}")
        
        logger.info("processing_message", case_id=case.id, phone=phone, phase=case.phase)
        
        # 3. Procesar según fase del caso (máquina de estados)
        reply = await self._handle_phase(case, text)
        
        # 4. Validar respuesta contra alucinaciones
        context = await self.memory.build_context_for_llm(case.id, text)
        hallucination_check = await self.hallucination.check_response(reply, context, text)
        
        if not hallucination_check.is_valid:
            logger.warning(
                "hallucination_detected",
                case_id=case.id,
                confidence=hallucination_check.confidence,
                flags=hallucination_check.flags
            )
            # Fallback a respuesta segura
            reply = "Disculpá, tuve un problema. ¿Podés reformular tu consulta?"
        
        # 5. Almacenar respuesta del asistente
        self.messages.add_message(case.id, "assistant", reply)
        await self.memory.store_immediate_memory(case.id, f"Asistente: {reply}")
        
        # 6. Guardar datos en memoria de sesión
        await self._update_session_memory(case)
        
        return MessageResponse(text=reply)
    
    async def _handle_phase(self, case, text: str) -> str:
        """Maneja el flujo según la fase actual del caso"""
        
        if case.phase == "inicio":
            return await self._phase_inicio(case)
        
        elif case.phase == "tipo_divorcio":
            return await self._phase_tipo_divorcio(case, text)
        
        elif case.phase == "nombre":
            return await self._phase_nombre(case, text)
        
        elif case.phase == "dni":
            return await self._phase_dni(case, text)
        
        elif case.phase == "fecha_nacimiento":
            return await self._phase_fecha_nacimiento(case, text)
        
        elif case.phase == "domicilio":
            return await self._phase_domicilio(case, text)
        
        elif case.phase == "documentacion":
            return await self._phase_documentacion(case, text)
        
        else:
            # Fallback: usar LLM con contexto
            return await self._llm_fallback(case, text)
    
    async def _phase_inicio(self, case) -> str:
        """Fase inicial: saludo y presentación"""
        case.phase = "tipo_divorcio"
        self.cases.update(case)
        return (
            "¡Hola! Soy tu asistente de la Defensoría Civil de San Rafael.\n"
            "Te voy a guiar paso a paso para iniciar tu trámite de divorcio.\n\n"
            "¿Qué tipo de divorcio querés iniciar: unilateral (solo vos) o conjunta (los dos)?"
        )
    
    async def _phase_tipo_divorcio(self, case, text: str) -> str:
        """Fase: selección de tipo de divorcio"""
        low = text.lower()
        if "unilateral" in low or "solo" in low:
            case.type = "unilateral"
            case.phase = "nombre"
            self.cases.update(case)
            return "Perfecto, divorcio unilateral. Ahora necesito algunos datos personales.\n\n¿Cuál es tu nombre completo?"
        elif "conjunta" in low or "ambos" in low or "los dos" in low:
            case.type = "conjunta"
            case.phase = "nombre"
            self.cases.update(case)
            return "Perfecto, divorcio conjunta. Ahora necesito algunos datos personales.\n\n¿Cuál es tu nombre completo?"
        else:
            return "Por favor respondé 'unilateral' si querés iniciar solo vos, o 'conjunta' si van a iniciar juntos."
    
    async def _phase_nombre(self, case, text: str) -> str:
        """Fase: recolección de nombre"""
        validation = self.validator_resp.validate_user_response(text, "nombre", "nombre completo")
        if not validation.is_valid:
            return "Necesito tu nombre completo real para continuar con el trámite legal. ¿Podés proporcionármelo?"
        
        case.nombre = text.strip()
        case.phase = "dni"
        self.cases.update(case)
        return f"Gracias, {case.nombre}. ¿Cuál es tu número de DNI?"
    
    async def _phase_dni(self, case, text: str) -> str:
        """Fase: recolección de DNI"""
        validation = self.validator_resp.validate_user_response(text, "dni", "documento")
        if not validation.is_valid:
            return "Ingresá un DNI válido de 7 u 8 dígitos, sin puntos ni espacios."
        
        case.dni = text.strip()
        case.phase = "fecha_nacimiento"
        self.cases.update(case)
        return "¿Cuál es tu fecha de nacimiento? Formato: DD/MM/AAAA"
    
    async def _phase_fecha_nacimiento(self, case, text: str) -> str:
        """Fase: validación de fecha de nacimiento"""
        result = self.validator_date.validate_birth_date(text)
        if not result.is_valid:
            errors = "\n- ".join(result.errors)
            return f"La fecha no es válida:\n- {errors}\n\nIngresá tu fecha de nacimiento en formato DD/MM/AAAA."
        
        # Almacenar fecha normalizada
        from datetime import datetime
        try:
            case.fecha_nacimiento = datetime.strptime(result.normalized_date, "%d/%m/%Y").date()
        except:
            pass
        
        case.phase = "domicilio"
        self.cases.update(case)
        return "✅ Perfecto. ¿Cuál es tu domicilio actual?\n\nEjemplo: San Martín 123, San Rafael, Mendoza"
    
    async def _phase_domicilio(self, case, text: str) -> str:
        """Fase: validación de domicilio"""
        result = self.validator_addr.validate_address(text, is_marital_address=False)
        if not result.is_valid:
            errors = "\n- ".join(result.errors)
            return f"La dirección está incompleta:\n- {errors}\n\nPor favor, indicá calle, número, ciudad y provincia."
        
        case.domicilio = result.normalized_address or text.strip()
        case.phase = "documentacion"
        case.status = "datos_completos"
        self.cases.update(case)
        
        # Generar resumen episódico
        summary = f"Usuario {case.nombre} completó datos personales para divorcio {case.type}. DNI: {case.dni}"
        await self.memory.store_episodic_memory(case.id, summary)
        
        return (
            "✅ Datos personales completos!\n\n"
            "📋 **Fase 2: Documentación**\n\n"
            "Ahora necesito que me envíes:\n"
            "1. Foto de tu DNI (frente y dorso)\n"
            "2. Acta de matrimonio\n\n"
            "Podés enviarlas en formato PDF o JPG."
        )
    
    async def _phase_documentacion(self, case, text: str) -> str:
        """Fase: documentación y consultas generales"""
        # Usar LLM con contexto para responder consultas
        return await self._llm_fallback(case, text)
    
    async def _llm_fallback(self, case, text: str) -> str:
        """Fallback: usar LLM con contexto completo"""
        context = await self.memory.build_context_for_llm(case.id, text)
        
        system_prompt = f"""Sos un asistente legal de la Defensoría Civil de San Rafael, Mendoza, Argentina.
Tu rol es ayudar con trámites de divorcio de forma amigable y profesional.

CONTEXTO DEL CASO:
{context}

REGLAS IMPORTANTES:
- Respondé en español argentino informal (vos, che, etc.)
- Sé breve y claro (máximo 3-4 oraciones)
- Si no sabés algo, admitilo y sugerí consultar con un operador
- NO inventes datos específicos (fechas, números, nombres)
- Para temas sensibles (violencia, menores), sugerí consulta presencial

Usuario pregunta: {text}

Respuesta:"""
        
        response = await self.llm.chat([{"role": "system", "content": system_prompt}])
        return response.strip()
    
    async def _update_session_memory(self, case):
        """Actualiza memoria de sesión con datos del caso"""
        session_data = {
            "type": case.type,
            "nombre": case.nombre,
            "dni": case.dni,
            "domicilio": case.domicilio,
            "phase": case.phase,
            "status": case.status
        }
        
        for key, value in session_data.items():
            if value:
                await self.memory.store_session_memory(case.id, key, value)
