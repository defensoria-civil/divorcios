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
from infrastructure.ocr.ocr_service_impl import MultiProviderOCRService
from infrastructure.messaging.waha_service_impl import WAHAWhatsAppService

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
        self.ocr = MultiProviderOCRService()
        self.whatsapp = WAHAWhatsAppService()
    
    async def execute(self, request: IncomingMessageRequest) -> MessageResponse:
        """Ejecuta el caso de uso"""
        phone = request.phone
        text = request.text
        media_id = request.media_id
        
        # 1. Obtener o crear caso
        case = self.cases.get_or_create_by_phone(phone)
        
        logger.info("processing_message", case_id=case.id, phone=phone, phase=case.phase, has_media=bool(media_id))
        
        # 2. Si hay media, procesar imagen
        if media_id:
            return await self._handle_media(case, media_id)
        
        # 3. Almacenar mensaje del usuario en DB y memoria
        self.messages.add_message(case.id, "user", text)
        await self.memory.store_immediate_memory(case.id, f"Usuario: {text}")
        
        # 4. Procesar según fase del caso (máquina de estados)
        reply = await self._handle_phase(case, text)
        
        # 5. Validar respuesta contra alucinaciones
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
        
        # 6. Almacenar respuesta del asistente
        self.messages.add_message(case.id, "assistant", reply)
        await self.memory.store_immediate_memory(case.id, f"Asistente: {reply}")
        
        # 7. Guardar datos en memoria de sesión
        await self._update_session_memory(case)
        
        return MessageResponse(text=reply)
    
    async def _handle_phase(self, case, text: str) -> str:
        """Maneja el flujo según la fase actual del caso"""
        
        if case.phase == "inicio":
            return await self._phase_inicio(case)
        
        elif case.phase == "tipo_divorcio":
            return await self._phase_tipo_divorcio(case, text)
        
        elif case.phase == "apellido":
            return await self._phase_apellido(case, text)
        
        elif case.phase == "nombres":
            return await self._phase_nombres(case, text)
        
        elif case.phase == "cuit":
            return await self._phase_cuit(case, text)
        
        elif case.phase == "fecha_nacimiento":
            return await self._phase_fecha_nacimiento(case, text)
        
        elif case.phase == "domicilio":
            return await self._phase_domicilio(case, text)
        
        elif case.phase == "apellido_conyuge":
            return await self._phase_apellido_conyuge(case, text)
        
        elif case.phase == "nombres_conyuge":
            return await self._phase_nombres_conyuge(case, text)
        
        elif case.phase == "econ_intro":
            return await self._phase_econ_intro(case, text)
        
        elif case.phase == "econ_situacion":
            return await self._phase_econ_situacion(case, text)
        
        elif case.phase == "econ_ingreso":
            return await self._phase_econ_ingreso(case, text)
        
        elif case.phase == "econ_vivienda":
            return await self._phase_econ_vivienda(case, text)
        
        elif case.phase == "econ_alquiler":
            return await self._phase_econ_alquiler(case, text)
        
        elif case.phase == "econ_patrimonio_inmuebles":
            return await self._phase_econ_patrimonio_inmuebles(case, text)
        
        elif case.phase == "econ_patrimonio_registrables":
            return await self._phase_econ_patrimonio_registrables(case, text)
        
        elif case.phase == "econ_cierre":
            return await self._phase_econ_cierre(case, text)
        
        elif case.phase == "doc_conyuge":
            return await self._phase_doc_conyuge(case, text)
        
        elif case.phase == "fecha_nacimiento_conyuge":
            return await self._phase_fecha_nacimiento_conyuge(case, text)
        
        elif case.phase == "domicilio_conyuge":
            return await self._phase_domicilio_conyuge(case, text)
        
        elif case.phase == "info_matrimonio":
            return await self._phase_info_matrimonio(case, text)
        
        elif case.phase == "hijos":
            return await self._phase_hijos(case, text)
        
        elif case.phase == "hijos_cuantos":
            return await self._phase_hijos_cuantos(case, text)
        
        elif case.phase == "hijo_nombre":
            return await self._phase_hijo_nombre(case, text)
        
        elif case.phase == "hijo_fecha":
            return await self._phase_hijo_fecha(case, text)
        
        elif case.phase == "hijo_mayor_eval":
            return await self._phase_hijo_mayor_eval(case, text)
        
        elif case.phase == "bienes":
            return await self._phase_bienes(case, text)
        
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
            case.phase = "apellido"
            self.cases.update(case)
            return "Perfecto, divorcio unilateral. Ahora necesito algunos datos personales.\n\n¿Cuál es tu apellido?"
        elif "conjunta" in low or "ambos" in low or "los dos" in low:
            case.type = "conjunta"
            case.phase = "apellido"
            self.cases.update(case)
            return "Perfecto, divorcio conjunta. Ahora necesito algunos datos personales.\n\n¿Cuál es tu apellido?"
        else:
            return "Por favor respondé 'unilateral' si querés iniciar solo vos, o 'conjunta' si van a iniciar juntos."
    
    async def _phase_apellido(self, case, text: str) -> str:
        """Fase: recolección de apellido"""
        apellido = text.strip().upper()  # Apellido en mayúsculas
        
        if len(apellido) < 2:
            return "Por favor, indicá tu apellido."
        
        case.apellido = apellido
        case.phase = "nombres"
        self.cases.update(case)
        return f"¿Cuáles son tus nombres? (sin apellido)"
    
    async def _phase_nombres(self, case, text: str) -> str:
        """Fase: recolección de nombres"""
        nombres = text.strip().title()  # Nombres capitalizados
        
        if len(nombres) < 2:
            return "Por favor, indicá tus nombres."
        
        case.nombres = nombres
        # Mantener el campo nombre para compatibilidad
        case.nombre = f"{nombres} {case.apellido}"
        case.phase = "cuit"
        self.cases.update(case)
        return f"Perfecto, {nombres} {case.apellido}. ¿Cuál es tu número de CUIT/CUIL? (11 dígitos)"
    
    async def _phase_cuit(self, case, text: str) -> str:
        """Fase: recolección de CUIT/CUIL y extracción de DNI"""
        import re
        
        # Limpiar el CUIT: quitar guiones y espacios
        cuit_clean = re.sub(r'[\s-]', '', text.strip())
        
        # Validar formato CUIT: 11 dígitos
        if not re.match(r'^\d{11}$', cuit_clean):
            return "El CUIT/CUIL debe tener 11 dígitos.\n\nEjemplo: 20-12345678-9 o 20123456789"
        
        # Extraer DNI del CUIT (dígitos 3 al 10)
        dni = cuit_clean[2:10]
        
        # Formatear CUIT con guiones para visualización
        cuit_formatted = f"{cuit_clean[0:2]}-{dni}-{cuit_clean[10]}"
        
        case.cuit = cuit_formatted
        case.dni = dni
        case.phase = "fecha_nacimiento"
        self.cases.update(case)
        
        return f"✅ CUIT/CUIL: {cuit_formatted}\nDNI extraído: {dni}\n\n¿Cuál es tu fecha de nacimiento? Formato: DD/MM/AAAA"
    
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
            return (
                "La dirección está incompleta:\n- " + errors +
                "\n\nPodés responder de estas formas:\n"
                "- Calle y número (ej: 'San Martín 123')\n"
                "- Ciudad y provincia (ej: 'San Rafael Mendoza' o 'San Rafael, Mendoza')\n"
                "- O todo junto: 'San Martín 123, San Rafael Mendoza'"
            )
        
        case.domicilio = result.normalized_address or text.strip()
        # Nueva sección: perfil económico (declaración jurada para BLSG)
        case.phase = "econ_intro"
        case.status = "datos_personales_completos"
        self.cases.update(case)
        
        # Generar resumen episódico
        summary = f"Usuario {case.nombre} completó datos personales para divorcio {case.type}. DNI: {case.dni}"
        await self.memory.store_episodic_memory(case.id, summary)
        
        return (
            "Antes de seguir, vamos a registrar algunos datos económicos para evaluar el Beneficio de Litigar sin Gastos (BLSG). "
            "Es una declaración jurada y luego un operador la va a revisar con tu documentación.\n\n"
            "¿Cuál es tu situación laboral? Opciones: desocupado/a, relación de dependencia, autónomo/monotributo, informal/changas, jubilación/pensión/beneficio u otro."
        )
    
    async def _phase_apellido_conyuge(self, case, text: str) -> str:
        """Fase: recolección de apellido del cónyuge"""
        apellido = text.strip().upper()
        
        if len(apellido) < 2:
            return "Por favor, indicá el apellido de tu cónyuge."
        
        case.apellido_conyuge = apellido
        case.phase = "nombres_conyuge"
        self.cases.update(case)
        return "¿Cuáles son los nombres de tu cónyuge? (sin apellido)"
    
    async def _phase_nombres_conyuge(self, case, text: str) -> str:
        """Fase: recolección de nombres del cónyuge"""
        nombres = text.strip().title()
        
        if len(nombres) < 2:
            return "Por favor, indicá los nombres de tu cónyuge."
        
        case.nombres_conyuge = nombres
        # Mantener nombre_conyuge para compatibilidad
        case.nombre_conyuge = f"{nombres} {case.apellido_conyuge}"
        # Aceptar DNI o CUIT/CUIL en el próximo paso
        case.phase = "doc_conyuge"
        self.cases.update(case)
        return (
            f"Perfecto, {nombres} {case.apellido_conyuge}. Ahora necesito el documento del cónyuge.\n\n"
            "Podés enviar:\n"
            "- Solo DNI (7 u 8 dígitos), o\n"
            "- CUIT/CUIL (11 dígitos, con o sin guiones)."
        )
    
    async def _phase_doc_conyuge(self, case, text: str) -> str:
        """Fase: documento del cónyuge (acepta DNI o CUIT/CUIL)."""
        import re
        value = re.sub(r'[\s-]', '', text.strip())
        if re.match(r'^\d{11}$', value):
            # CUIT/CUIL
            dni = value[2:10]
            case.cuit_conyuge = f"{value[0:2]}-{dni}-{value[10]}"
            case.dni_conyuge = dni
        elif re.match(r'^\d{7,8}$', value):
            # Solo DNI
            case.dni_conyuge = value
        else:
            return (
                "El documento debe ser DNI (7/8 dígitos) o CUIT/CUIL (11 dígitos).\n"
                "Ejemplos: 12345678 o 27-29933256-8"
            )
        # Siguiente: fecha de nacimiento del cónyuge
        case.phase = "fecha_nacimiento_conyuge"
        self.cases.update(case)
        return "Ahora, ¿podrías indicarme la fecha de nacimiento del cónyuge? (DD/MM/AAAA)"
    
    async def _phase_fecha_nacimiento_conyuge(self, case, text: str) -> str:
        """Fase: fecha de nacimiento del cónyuge"""
        result = self.validator_date.validate_birth_date(text)
        if not result.is_valid:
            errors = "\n- ".join(result.errors)
            return f"La fecha no es válida:\n- {errors}\n\nIngresá la fecha de nacimiento en formato DD/MM/AAAA."
        from datetime import datetime
        try:
            case.fecha_nacimiento_conyuge = datetime.strptime(result.normalized_date, "%d/%m/%Y").date()
        except:
            pass
        case.phase = "domicilio_conyuge"
        self.cases.update(case)
        return "Gracias. ¿Cuál es el domicilio actual del cónyuge?\n\nEjemplo: San Martín 123, San Rafael, Mendoza"

    async def _phase_domicilio_conyuge(self, case, text: str) -> str:
        """Fase: domicilio del cónyuge"""
        result = self.validator_addr.validate_address(text, is_marital_address=False)
        if not result.is_valid:
            errors = "\n- ".join(result.errors)
            return (
                "La dirección está incompleta:\n- " + errors +
                "\n\nPodés responder de estas formas:\n"
                "- Calle y número (ej: 'San Martín 123')\n"
                "- Ciudad y provincia (ej: 'San Rafael Mendoza' o 'San Rafael, Mendoza')\n"
                "- O todo junto: 'San Martín 123, San Rafael Mendoza'"
            )
        case.domicilio_conyuge = result.normalized_address or text.strip()
        case.phase = "info_matrimonio"
        self.cases.update(case)
        return (
            "Gracias, anoté el domicilio del cónyuge.\n\n"
            "Ahora, para avanzar con el trámite, necesito saber la fecha y el lugar del casamiento."
        )

    async def _phase_info_matrimonio(self, case, text: str) -> str:
        """Fase: información del matrimonio con parsing de lenguaje natural"""
        import re
        from datetime import datetime
        
        # Buscar fecha en formato DD/MM/AAAA o DD-MM-AAAA
        fecha_match = re.search(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', text)
        if not fecha_match:
            return "Por favor, indicá la fecha y lugar del matrimonio.\n\nEjemplo: 'Nos casamos el 15/03/2005 en San Rafael' o '15/03/2005, San Rafael, Mendoza'"
        
        # Validar y guardar fecha
        try:
            fecha_str = f"{fecha_match.group(1)}/{fecha_match.group(2)}/{fecha_match.group(3)}"
            case.fecha_matrimonio = datetime.strptime(fecha_str, "%d/%m/%Y").date()
        except:
            return "La fecha no es válida. Usá el formato DD/MM/AAAA.\n\nEjemplo: 15/03/2005 en San Rafael, Mendoza"
        
        # Extraer lugar con regex más robusto
        # Remover frases comunes antes del lugar
        lugar_text = text.lower()
        lugar_text = re.sub(r'(nos\s+)?casamos?', '', lugar_text)
        lugar_text = re.sub(r'\b(en|el|la)\b', ' ', lugar_text)
        lugar_text = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b', '', lugar_text)  # Quitar fecha
        
        # Limpiar espacios múltiples
        lugar = ' '.join(lugar_text.split()).strip()
        
        # Capitalizar correctamente
        lugar = lugar.title()
        
        # Validar que tengamos algo mínimo
        if len(lugar) < 5 or lugar.lower() in ['el', 'en', 'la', 'nos', 'casamos']:
            return f"Ya anoté la fecha {fecha_str}. ¿En qué ciudad y provincia se casaron?\n\nEjemplo: 'San Rafael, Mendoza' o 'San Rafael Mendoza'"
        
        case.lugar_matrimonio = lugar
        case.phase = "hijos"
        self.cases.update(case)
        
        return (
            f"¡Perfecto! Ya anoté que se casaron el {fecha_str} en {case.lugar_matrimonio}.\n\n"
            "Ahora vamos a registrar a los hijos que corresponda incluir en el convenio.\n\n"
            "Solo se incluyen: (a) menores de 18; (b) de 18 a 25 que estudian y no son económicamente independientes; o (c) de cualquier edad con CUD.\n\n"
            "¿Tienen hijos en común con estas características? Si no, respondé 'no'."
        )
    
    async def _phase_hijos(self, case, text: str) -> str:
        """Fase: información sobre hijos (introducción y decisión)"""
        low = text.lower().strip()
        
        if low in ['no', 'no tenemos', 'ninguno', 'no hay']:
            case.tiene_hijos = False
            case.phase = "bienes"
            self.cases.update(case)
            return (
                "Entendido. No van a incluir hijos en el convenio.\n\n"
                "¿Tienen bienes en común? (casa, auto, cuentas bancarias, etc.)\n\n"
                "Si no tienen, respondé 'no'."
            )
        
        # Si responden afirmativamente, pedir cantidad bajo el criterio
        case.tiene_hijos = True
        self.cases.update(case)
        case.phase = "hijos_cuantos"
        return (
            "Perfecto. Solo incluiremos hijos con las características indicadas.\n"
            "¿Cuántos hijos en común con esas características desean declarar?"
        )
    
    async def _phase_hijos_cuantos(self, case, text: str) -> str:
        """Pregunta la cantidad de hijos a declarar y prepara el flujo por hijo"""
        import re
        m = re.search(r"\d+", text)
        if not m:
            return "Indicá un número (0, 1, 2, ...). Si prefieren no incluir, respondé 'no'."
        total = int(m.group())
        if total <= 0:
            case.tiene_hijos = False
            case.phase = "bienes"
            self.cases.update(case)
            return (
                "Entendido. No van a incluir hijos en el convenio.\n\n"
                "¿Tienen bienes en común? (casa, auto, cuentas bancarias, etc.)\n\n"
                "Si no tienen, respondé 'no'."
            )
        # Guardar en memoria de sesión
        await self.memory.store_session_memory(case.id, "hijos_total", total)
        await self.memory.store_session_memory(case.id, "hijos_index", 0)
        case.phase = "hijo_nombre"
        self.cases.update(case)
        return "Decime el nombre completo del hijo/a 1"
    
    async def _phase_hijo_nombre(self, case, text: str) -> str:
        nombre_hijo = text.strip().title()
        if len(nombre_hijo) < 2:
            return "Indicá el nombre completo, por favor."
        # Guardar temporalmente en memoria
        await self.memory.store_session_memory(case.id, "hijo_actual_nombre", nombre_hijo)
        case.phase = "hijo_fecha"
        self.cases.update(case)
        return f"¿Cuál es la fecha de nacimiento de {nombre_hijo}? (DD/MM/AAAA)"
    
    async def _phase_hijo_fecha(self, case, text: str) -> str:
        from datetime import datetime, date
        import re
        # Parse fecha
        m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", text)
        if not m:
            return "Ingresá la fecha en formato DD/MM/AAAA."
        try:
            dob = datetime.strptime(f"{m.group(1)}/{m.group(2)}/{m.group(3)}", "%d/%m/%Y").date()
        except:
            return "La fecha no es válida. Usá el formato DD/MM/AAAA."
        # Calcular edad
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        # Obtener nombre y contadores
        data = await self.memory.retrieve_session_data(case.id)
        nombre_hijo = data.get("hijo_actual_nombre", "Hijo")
        total = int(data.get("hijos_total", 1) or 1)
        index = int(data.get("hijos_index", 0) or 0)
        # Decidir inclusión
        if age < 18:
            motivo = "MENOR_18"
            incluido = True
        else:
            # Requiere evaluación adicional
            await self.memory.store_session_memory(case.id, "hijo_actual_edad", age)
            case.phase = "hijo_mayor_eval"
            self.cases.update(case)
            return (
                f"{nombre_hijo} tiene {age} años. Para incluirlo, indicá si:\n"
                "- Tiene CUD vigente (respondé 'CUD'), o\n"
                "- Tiene entre 18 y 25, estudia y no es económicamente independiente (respondé 'ESTUDIA'), o\n"
                "- Ninguna de las anteriores (respondé 'NO')."
            )
        # Registrar y avanzar
        linea = f"{nombre_hijo} - Fecha nac.: {dob.strftime('%d/%m/%Y')} - Motivo: {motivo}"
        case.info_hijos = (case.info_hijos + "\n" if case.info_hijos else "") + linea
        # Incrementar índice
        index += 1
        await self.memory.store_session_memory(case.id, "hijos_index", index)
        self.cases.update(case)
        if index >= total:
            case.phase = "bienes"
            self.cases.update(case)
            return (
                "Datos de hijos registrados.\n\n"
                "¿Tienen bienes en común? (casa, auto, cuentas bancarias, deudas, etc.)\n\n"
                "Si no tienen, respondé 'no'."
            )
        else:
            case.phase = "hijo_nombre"
            self.cases.update(case)
            return f"Decime el nombre completo del hijo/a {index+1}"
    
    async def _phase_hijo_mayor_eval(self, case, text: str) -> str:
        low = text.lower().strip()
        data = await self.memory.retrieve_session_data(case.id)
        nombre_hijo = data.get("hijo_actual_nombre", "Hijo")
        age = int(data.get("hijo_actual_edad", 18) or 18)
        total = int(data.get("hijos_total", 1) or 1)
        index = int(data.get("hijos_index", 0) or 0)
        if low in ["cud", "tiene cud", "discapacidad", "si cud"]:
            motivo = "DISCAPACIDAD_CUD"
            incluido = True
        elif low in ["estudia", "18-25", "estudia_dep", "dep", "estudia y no es independiente"]:
            motivo = "ESTUDIA_18A25_DEP" if 18 <= age <= 25 else "NO_CRITERIO"
            incluido = 18 <= age <= 25
        else:
            motivo = "NO_CRITERIO"
            incluido = False
        # Registrar línea
        linea = f"{nombre_hijo} - Edad: {age} - Motivo: {motivo} - {'Incluido' if incluido else 'Excluido'}"
        case.info_hijos = (case.info_hijos + "\n" if case.info_hijos else "") + linea
        # Siguiente
        index += 1
        await self.memory.store_session_memory(case.id, "hijos_index", index)
        if index >= total:
            case.phase = "bienes"
            self.cases.update(case)
            return (
                "Datos de hijos registrados.\n\n"
                "¿Tienen bienes en común? (casa, auto, cuentas bancarias, deudas, etc.)\n\n"
                "Si no tienen, respondé 'no'."
            )
        else:
            case.phase = "hijo_nombre"
            self.cases.update(case)
            return f"Decime el nombre completo del hijo/a {index+1}"
    
    async def _phase_bienes(self, case, text: str) -> str:
        """Fase: información sobre bienes"""
        low = text.lower().strip()
        
        if low in ['no', 'no tenemos', 'ninguno', 'no hay', 'nada']:
            case.tiene_bienes = False
            case.phase = "documentacion"
            case.status = "info_completa"
            self.cases.update(case)
            
            # Generar resumen episódico
            summary = f"Usuario {case.nombre} completó toda la información del divorcio. Cónyuge: {case.nombre_conyuge}. Hijos: {'Sí' if case.tiene_hijos else 'No'}. Bienes: No"
            await self.memory.store_episodic_memory(case.id, summary)
            
            return (
                "✅ ¡Excelente! Toda la información está completa.\n\n"
                "📋 **Resumen:**\n"
                f"- Tipo: Divorcio {case.type}\n"
                f"- Solicitante: {case.nombre}\n"
                f"- Cónyuge: {case.nombre_conyuge}\n"
                f"- Hijos en común: {'Sí' if case.tiene_hijos else 'No'}\n"
                f"- Bienes en común: No\n\n"
                "📝 **Próximos pasos:**\n"
                "1. En las próximas 24-48hs un operador de la Defendería va a revisar tu caso\n"
                "2. Te contactaremos para coordinar la presentación de documentación\n"
                "3. Redactaremos la demanda de divorcio\n\n"
                "¿Tenés alguna consulta mientras tanto?"
            )
        
        # Si tienen bienes, guardar la info
        case.tiene_bienes = True
        case.info_bienes = text.strip()
        case.phase = "documentacion"
        case.status = "info_completa"
        self.cases.update(case)
        
        # Generar resumen episódico
        summary = f"Usuario {case.nombre} completó toda la información. Cónyuge: {case.nombre_conyuge}. Hijos: {'Sí' if case.tiene_hijos else 'No'}. Bienes: Sí"
        await self.memory.store_episodic_memory(case.id, summary)
        
        return (
            f"¡Perfecto! Anoté los bienes: {text}\n\n"
            "✅ Toda la información está completa.\n\n"
            "📋 **Resumen:**\n"
            f"- Tipo: Divorcio {case.type}\n"
            f"- Solicitante: {case.nombre}\n"
            f"- Cónyuge: {case.nombre_conyuge}\n"
            f"- Hijos en común: {'Sí' if case.tiene_hijos else 'No'}\n"
            f"- Bienes en común: Sí\n\n"
            "📝 **Próximos pasos:**\n"
            "1. En las próximas 24-48hs un operador va a revisar tu caso\n"
            "2. Te contactaremos para coordinar documentación y partición de bienes\n"
            "3. Redactaremos la propuesta de convenio y la demanda\n\n"
            "¿Tenés alguna consulta?"
        )
    
    async def _phase_documentacion(self, case, text: str) -> str:
        """Fase: documentación y consultas generales"""
        # Usar LLM con contexto para responder consultas
        return await self._llm_fallback(case, text)
    
    async def _llm_fallback(self, case, text: str) -> str:
        """Fallback: usar LLM con contexto completo"""
        context = await self.memory.build_context_for_llm(case.id, text)
        
        system_prompt = f"""Sos un asistente legal de la Defensoría Civil de San Rafael, Mendoza, Argentina.
Tu rol es ayudar con trámites de divorcio de forma cercana, clara y profesional.

CONTEXTO DEL CASO:
{context}

REGLAS IMPORTANTES:
- Respondé en español argentino cercano y respetuoso (usá 'vos'). Evitá muletillas como "che", "ay", "dale" y exclamaciones innecesarias.
- Sé breve y claro (máximo 3-4 oraciones)
- Si no sabés algo, admitilo y sugerí consultar con un operador
- NO inventes datos específicos (fechas, números, nombres)
- No repreguntes información ya registrada; usá los datos guardados. Si el usuario quiere cambiarlos, ofrecé: "¿Querés editar X?".
- Para temas sensibles (violencia, menores), sugerí consulta presencial

Usuario pregunta: {text}

Respuesta:"""
        
        response = await self.llm.chat([{"role": "system", "content": system_prompt}])
        return response.strip()
    
    # ===== Sección PERFIL ECONÓMICO =====
    async def _phase_econ_intro(self, case, text: str) -> str:
        # Primer mensaje ya advirtió; pasamos a situacion laboral interpretando la respuesta
        return await self._phase_econ_situacion(case, text)

    async def _phase_econ_situacion(self, case, text: str) -> str:
        low = text.lower().strip()
        mapping = {
            "desocupado": "desocupado",
            "desempleado": "desocupado",
            "dependencia": "dependencia",
            "empleado": "dependencia",
            "autonomo": "autonomo",
            "monotributo": "autonomo",
            "monotributista": "autonomo",
            "informal": "informal",
            "changas": "informal",
            "jubil": "jubilado",
            "pension": "jubilado",
            "beneficio": "jubilado",
        }
        cat = None
        for k, v in mapping.items():
            if k in low:
                cat = v
                break
        if not cat:
            cat = "otro"
        case.situacion_laboral = cat
        # Tips documentales
        if cat == "desocupado":
            case.econ_razones = (case.econ_razones or "") + "\nDoc: Certificado Negativo ANSES: https://servicioswww.anses.gob.ar/censite/index.aspx"
        elif cat == "dependencia":
            case.econ_razones = (case.econ_razones or "") + "\nDoc: último recibo de sueldo"
        elif cat == "autonomo":
            case.econ_razones = (case.econ_razones or "") + "\nDoc: constancia/posición AFIP"
        self.cases.update(case)
        # Pedir ingreso si corresponde
        if cat in ("dependencia", "autonomo", "informal", "jubilado"):
            case.phase = "econ_ingreso"
            self.cases.update(case)
            return "¿Cuál es tu ingreso mensual neto? Indicá solo el monto en pesos (ej: 250000)."
        # Si desocupado u otro, pasar a vivienda
        case.phase = "econ_vivienda"
        self.cases.update(case)
        return "¿Tu vivienda es propia, alquilada o cedida/prestada?"

    async def _phase_econ_ingreso(self, case, text: str) -> str:
        import re
        s = text.replace(".", "").replace(",", "").lower()
        s = s.replace("k", "000")
        m = re.search(r"\d+", s)
        if not m:
            return "Indicá un número en pesos, por favor (ej: 250000)."
        case.ingreso_mensual_neto = int(m.group())
        self.cases.update(case)
        case.phase = "econ_vivienda"
        return "¿Tu vivienda es propia, alquilada o cedida/prestada?"

    async def _phase_econ_vivienda(self, case, text: str) -> str:
        low = text.lower()
        if "alquil" in low:
            case.vivienda_tipo = "alquilada"
            case.phase = "econ_alquiler"
            self.cases.update(case)
            return "¿Cuánto pagás por mes de alquiler? (monto en pesos)"
        elif "prop" in low:
            case.vivienda_tipo = "propia"
        else:
            case.vivienda_tipo = "cedida"
        self.cases.update(case)
        case.phase = "econ_patrimonio_inmuebles"
        return "¿Tenés inmuebles a tu nombre? Si sí, indicá ciudad/provincia (ej: 'casa en San Rafael, Mendoza'). Podés responder 'no'."

    async def _phase_econ_alquiler(self, case, text: str) -> str:
        import re
        m = re.search(r"\d+", text.replace(".", "").replace(",", ""))
        if not m:
            return "Indicá un número en pesos, por favor (ej: 120000)."
        case.alquiler_mensual = int(m.group())
        self.cases.update(case)
        case.phase = "econ_patrimonio_inmuebles"
        return "¿Tenés inmuebles a tu nombre? Si sí, indicá ciudad/provincia. Podés responder 'no'."

    async def _phase_econ_patrimonio_inmuebles(self, case, text: str) -> str:
        if text.strip().lower() not in ("no", "ninguno", "no tengo"):
            case.patrimonio_inmuebles = text.strip()
        self.cases.update(case)
        case.phase = "econ_patrimonio_registrables"
        return "¿Tenés vehículos u otros bienes registrables? Indicá tipo, año, dominio y modelo (ej: 'auto 2015 ABC123 Ford Fiesta'). Podés responder 'no'."

    async def _phase_econ_patrimonio_registrables(self, case, text: str) -> str:
        if text.strip().lower() not in ("no", "ninguno", "no tengo"):
            case.patrimonio_registrables = text.strip()
        self.cases.update(case)
        # calcular preliminar y cerrar
        case.phase = "econ_cierre"
        return await self._phase_econ_cierre(case, "")

    def _compute_econ_precheck(self, case):
        import os
        try:
            smvm = int(os.getenv("SMVM_AMOUNT", "250000"))
        except:
            smvm = 250000
        ingreso = case.ingreso_mensual_neto or 0
        alquiler = case.alquiler_mensual or 0
        disponible = max(0, ingreso - alquiler)
        # Heurísticas simples
        per_capita = disponible  # sin cargas por ahora
        elegible = (per_capita <= 1.5 * smvm) or (ingreso <= 2.0 * smvm) or (case.vivienda_tipo == "cedida") or (case.situacion_laboral == "desocupado")
        razones = {
            "smvm": smvm,
            "ingreso": ingreso,
            "alquiler": alquiler,
            "disponible": disponible,
            "criterios": [
                "per_capita <= 1.5*SMVM",
                "ingreso <= 2*SMVM",
                "vivienda cedida/prestada",
                "desocupado/a",
            ],
        }
        return elegible, razones

    async def _phase_econ_cierre(self, case, _: str) -> str:
        elegible, razones = self._compute_econ_precheck(case)
        case.econ_elegible_preliminar = bool(elegible)
        import json
        try:
            case.econ_razones = json.dumps(razones, ensure_ascii=False)
        except Exception:
            case.econ_razones = str(razones)
        self.cases.update(case)
        # Continuar con datos del cónyuge
        case.phase = "apellido_conyuge"
        self.cases.update(case)
        status = "calificás" if elegible else "a priori no calificás"
        aclaracion = "Esto es preliminar y puede revisarse por un operador luego de ver tu documentación."
        # Añadir recordatorio documental según situación laboral
        extra = ""
        if (case.situacion_laboral or "") == "desocupado":
            extra = "\nRecordá: Certificado Negativo de ANSES https://servicioswww.anses.gob.ar/censite/index.aspx"
        elif (case.situacion_laboral or "") == "dependencia":
            extra = "\nRecordá: último recibo de sueldo."
        elif (case.situacion_laboral or "") == "autonomo":
            extra = "\nRecordá: constancia/posición AFIP."
        return (
            f"Gracias. Registré tu información económica. Según lo declarado, {status} para BLSG. {aclaracion}.{extra}\n\n"
            "Ahora necesito información sobre tu cónyuge.\n\n¿Cuál es el apellido de tu cónyuge?"
        )

    # ===== Fin PERFIL ECONÓMICO =====

    async def _update_session_memory(self, case):
        """Actualiza memoria de sesión con datos del caso"""
        session_data = {
            "type": case.type,
            "nombre": case.nombre,
            "dni": case.dni,
            "domicilio": case.domicilio,
            "nombre_conyuge": case.nombre_conyuge,
            "tiene_hijos": case.tiene_hijos,
            "info_hijos": case.info_hijos,
            "tiene_bienes": case.tiene_bienes,
            "info_bienes": case.info_bienes,
            "phase": case.phase,
            "status": case.status
        }
        
        for key, value in session_data.items():
            if value is not None and value != "":
                await self.memory.store_session_memory(case.id, key, value)
    
    async def _handle_media(self, case, media_id: str) -> MessageResponse:
        """Procesa imagen enviada por el usuario (DNI o acta de matrimonio)"""
        
        try:
            # 1. Descargar imagen desde WhatsApp
            logger.info("downloading_media", case_id=case.id, media_id=media_id)
            image_bytes = await self.whatsapp.download_media(media_id)
            
            # 2. Determinar tipo de documento según fase del caso
            if case.phase == "documentacion":
                # En fase de documentación, puede ser DNI o acta
                # Intentamos detectar primero si es DNI
                if not case.dni_image_url:  # Aún no tiene DNI
                    return await self._process_dni_image(case, image_bytes, media_id)
                else:  # Ya tiene DNI, debe ser acta de matrimonio
                    return await self._process_marriage_cert_image(case, image_bytes, media_id)
            
            elif case.phase == "dni":
                # Usuario está en fase de proporcionar DNI, puede enviar foto directamente
                return await self._process_dni_image(case, image_bytes, media_id)
            
            else:
                # Fase no esperada para recibir imágenes
                return MessageResponse(
                    text="Gracias por la imagen, pero todavía no estamos en la etapa de documentación. "
                         "Primero necesito completar tus datos personales."
                )
        
        except Exception as e:
            logger.error("media_processing_error", case_id=case.id, media_id=media_id, error=str(e))
            return MessageResponse(
                text="Disculpá, tuve un problema procesando la imagen. ¿Podés intentar enviarla de nuevo?"
            )
    
    async def _process_dni_image(self, case, image_bytes: bytes, media_id: str) -> MessageResponse:
        """Procesa imagen de DNI usando OCR"""
        
        logger.info("processing_dni_image", case_id=case.id)
        
        # Ejecutar OCR
        ocr_result = await self.ocr.extract_dni_data(image_bytes)
        
        if not ocr_result.success or ocr_result.confidence < 0.6:
            errors_text = "\n- ".join(ocr_result.errors) if ocr_result.errors else "Imagen poco clara"
            return MessageResponse(
                text=f"No pude procesar el DNI correctamente:\n- {errors_text}\n\n"
                     "Por favor, enviá una foto más clara del DNI (frente y dorso)."
            )
        
        # Extraer datos
        dni_data = ocr_result.data
        
        # Actualizar caso con datos extraídos
        if dni_data.get("numero_documento"):
            case.dni = str(dni_data["numero_documento"])
        if dni_data.get("nombre_completo"):
            case.nombre = dni_data["nombre_completo"]
        if dni_data.get("fecha_nacimiento"):
            from datetime import datetime
            try:
                case.fecha_nacimiento = datetime.strptime(dni_data["fecha_nacimiento"], "%d/%m/%Y").date()
            except:
                pass
        
        # Guardar referencia a la imagen
        case.dni_image_url = media_id  # Usamos media_id como referencia
        
        # Avanzar fase si estamos en fase DNI
        if case.phase == "dni":
            case.phase = "fecha_nacimiento"
        
        self.cases.update(case)
        
        # Guardar en memoria
        await self.memory.store_immediate_memory(case.id, f"Usuario envió DNI. Datos extraídos: {dni_data}")
        
        # Respuesta con confirmación
        confidence_emoji = "✅" if ocr_result.confidence > 0.8 else "⚠️"
        return MessageResponse(
            text=f"{confidence_emoji} DNI procesado correctamente.\n\n"
                 f"**Datos detectados:**\n"
                 f"- DNI: {case.dni or 'No detectado'}\n"
                 f"- Nombre: {case.nombre or 'No detectado'}\n\n"
                 f"¿Los datos son correctos? Si hay algún error, decime cuál es para corregirlo."
        )
    
    async def _process_marriage_cert_image(self, case, image_bytes: bytes, media_id: str) -> MessageResponse:
        """Procesa imagen de acta de matrimonio usando OCR"""
        
        logger.info("processing_marriage_cert", case_id=case.id)
        
        # Ejecutar OCR
        ocr_result = await self.ocr.extract_marriage_certificate_data(image_bytes)
        
        if not ocr_result.success or ocr_result.confidence < 0.6:
            errors_text = "\n- ".join(ocr_result.errors) if ocr_result.errors else "Imagen poco clara"
            return MessageResponse(
                text=f"No pude procesar el acta de matrimonio correctamente:\n- {errors_text}\n\n"
                     "Por favor, enviá una foto más clara del acta."
            )
        
        # Extraer datos
        cert_data = ocr_result.data
        
        # Actualizar caso con datos del matrimonio
        if cert_data.get("fecha_matrimonio"):
            from datetime import datetime
            try:
                case.fecha_matrimonio = datetime.strptime(cert_data["fecha_matrimonio"], "%d/%m/%Y").date()
            except:
                pass
        
        if cert_data.get("lugar_matrimonio"):
            case.lugar_matrimonio = cert_data["lugar_matrimonio"]
        
        # Guardar referencia a la imagen
        case.marriage_cert_url = media_id
        
        # Actualizar estado: documentación completa
        case.status = "documentacion_completa"
        self.cases.update(case)
        
        # Guardar en memoria
        await self.memory.store_immediate_memory(case.id, f"Usuario envió acta de matrimonio. Datos extraídos: {cert_data}")
        
        # Generar resumen episódico
        summary = f"Usuario {case.nombre} completó toda la documentación. Fecha matrimonio: {case.fecha_matrimonio}"
        await self.memory.store_episodic_memory(case.id, summary)
        
        # Respuesta con confirmación y próximos pasos
        confidence_emoji = "✅" if ocr_result.confidence > 0.8 else "⚠️"
        return MessageResponse(
            text=f"{confidence_emoji} Acta de matrimonio procesada correctamente.\n\n"
                 f"**Datos detectados:**\n"
                 f"- Fecha matrimonio: {cert_data.get('fecha_matrimonio', 'No detectado')}\n"
                 f"- Lugar: {cert_data.get('lugar_matrimonio', 'No detectado')}\n\n"
                 f"🎉 **¡Documentación completa!**\n\n"
                 f"Ya tengo toda la información necesaria. En las próximas 48hs un operador de la Defensoría "
                 f"va a revisar tu caso y te va a contactar para coordinar los siguientes pasos.\n\n"
                 f"¿Tenés alguna consulta mientras tanto?"
        )
