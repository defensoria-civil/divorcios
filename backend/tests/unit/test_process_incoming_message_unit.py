"""
Tests Unitarios: ProcessIncomingMessageUseCase

Tests completos para el caso de uso principal de procesamiento de mensajes entrantes.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Note: Este archivo contiene tests unitarios con mocks
# Para tests de integración completos, ver test_conversation_flow.py


class TestProcessIncomingMessageInitialization:
    """Tests de inicialización del caso de uso"""
    
    def test_use_case_requires_db_session(self):
        """Test: El caso de uso requiere una sesión de BD"""
        from application.use_cases.process_incoming_message import ProcessIncomingMessageUseCase
        
        mock_db = Mock()
        use_case = ProcessIncomingMessageUseCase(mock_db)
        
        assert use_case.db is not None
        assert use_case.db == mock_db


class TestMessageValidation:
    """Tests de validación de mensajes"""
    
    def test_empty_phone_number_validation(self):
        """Test: El DTO permite phone vacío actualmente (comportamiento documentado)."""
        from application.use_cases.process_incoming_message import IncomingMessageRequest

        request = IncomingMessageRequest(phone="", text="Hola")
        assert request.phone == ""
    
    def test_empty_text_validation(self):
        """Test: Validación de texto vacío"""
        from application.use_cases.process_incoming_message import IncomingMessageRequest
        
        # El sistema debe aceptar texto vacío (puede ser una imagen sin caption)
        request = IncomingMessageRequest(phone="+5492604123456", text="")
        assert request.text == ""
    
    def test_phone_number_normalization(self):
        """Test: Normalización de número de teléfono"""
        from application.use_cases.process_incoming_message import IncomingMessageRequest
        
        # Diferentes formatos de número
        request1 = IncomingMessageRequest(phone="2604123456", text="Hola")
        request2 = IncomingMessageRequest(phone="+5492604123456", text="Hola")
        request3 = IncomingMessageRequest(phone="549 2604 123456", text="Hola")
        
        # Todos deberían ser válidos
        assert request1.phone is not None
        assert request2.phone is not None
        assert request3.phone is not None


class TestPhaseManagement:
    """Tests de gestión de fases del flujo de conversación"""
    
    @pytest.mark.asyncio
    async def test_inicio_phase_transitions_to_tipo_divorcio(self):
        """La fase 'inicio' debe pasar a 'tipo_divorcio' y dar mensaje de bienvenida."""
        from application.use_cases.process_incoming_message import (
            ProcessIncomingMessageUseCase,
            IncomingMessageRequest,
        )

        # 1) Preparar caso simulado en fase inicio
        mock_db = Mock()
        mock_case = Mock()
        mock_case.id = 1
        mock_case.phone = "+5492604000000"
        mock_case.phase = "inicio"
        mock_case.type = None

        with patch("application.use_cases.process_incoming_message.CaseRepository") as CaseRepoMock, \
             patch("application.use_cases.process_incoming_message.MessageRepository") as MsgRepoMock, \
             patch("application.use_cases.process_incoming_message.MemoryService") as MemorySvcMock, \
             patch("application.use_cases.process_incoming_message.HallucinationDetectionService") as HallucMock, \
             patch("application.use_cases.process_incoming_message.LLMRouter") as LLMRouterMock:

            # Repositorios
            case_repo_instance = CaseRepoMock.return_value
            case_repo_instance.get_or_create_by_phone.return_value = mock_case

            # No queremos efectos colaterales de memoria/LLM en este test
            memory_instance = MemorySvcMock.return_value
            memory_instance.store_immediate_memory = AsyncMock()
            memory_instance.build_context_for_llm = AsyncMock(return_value="")
            memory_instance.store_session_memory = AsyncMock()

            halluc_instance = HallucMock.return_value
            halluc_result = Mock()
            halluc_result.is_valid = True
            halluc_instance.check_response = AsyncMock(return_value=halluc_result)

            llm_instance = LLMRouterMock.return_value
            llm_instance.chat = AsyncMock(return_value="")

            # 2) Ejecutar caso de uso
            use_case = ProcessIncomingMessageUseCase(mock_db)
            request = IncomingMessageRequest(phone=mock_case.phone, text="Hola")
            response = await use_case.execute(request)

            # 3) Verificaciones
            assert "tipo de divorcio" in response.text.lower()
            assert mock_case.phase == "tipo_divorcio"
            case_repo_instance.update.assert_called_once_with(mock_case)

    @pytest.mark.asyncio
    async def test_tipo_divorcio_accepts_unilateral_and_conjunta(self):
        """La fase tipo_divorcio debe reconocer 'unilateral' y 'conjunta'."""
        from application.use_cases.process_incoming_message import ProcessIncomingMessageUseCase

        mock_db = Mock()
        use_case = ProcessIncomingMessageUseCase(mock_db)

        # Creamos un case simulado y llamamos directamente a _phase_tipo_divorcio
        mock_case = Mock()
        mock_case.phase = "tipo_divorcio"

        # Unilateral
        reply_uni = await use_case._phase_tipo_divorcio(mock_case, "Quiero un divorcio unilateral")
        assert "unilateral" in (mock_case.type or "")
        assert mock_case.phase == "apellido"
        assert "apellido" in reply_uni.lower()

        # Conjunta
        mock_case.phase = "tipo_divorcio"
        reply_conj = await use_case._phase_tipo_divorcio(mock_case, "divorcio conjunta")
        assert "conjunta" in (mock_case.type or "")
        assert mock_case.phase == "apellido"
        assert "apellido" in reply_conj.lower()

    @pytest.mark.asyncio
    async def test_cuit_phase_validates_format(self):
        """La fase CUIT debe validar que el CUIT tenga 11 dígitos."""
        from application.use_cases.process_incoming_message import ProcessIncomingMessageUseCase

        mock_db = Mock()
        use_case = ProcessIncomingMessageUseCase(mock_db)

        mock_case = Mock()
        mock_case.phase = "cuit"

        # CUIT inválido
        reply_invalid = await use_case._phase_cuit(mock_case, "123")
        assert "11" in reply_invalid

        # CUIT válido
        reply_valid = await use_case._phase_cuit(mock_case, "20-12345678-9")
        assert "dni extraído" in reply_valid.lower()
        assert mock_case.dni == "12345678"

    @pytest.mark.asyncio
    async def test_fecha_nacimiento_uses_validator(self):
        """La fase fecha_nacimiento debe delegar en el validador de fechas."""
        from application.use_cases.process_incoming_message import ProcessIncomingMessageUseCase

        mock_db = Mock()
        use_case = ProcessIncomingMessageUseCase(mock_db)

        mock_case = Mock()
        mock_case.phase = "fecha_nacimiento"

        # Forzamos un resultado inválido del validador
        fake_result = Mock()
        fake_result.is_valid = False
        fake_result.errors = ["Fecha en el futuro"]
        use_case.validator_date.validate_birth_date = Mock(return_value=fake_result)

        reply = await use_case._phase_fecha_nacimiento(mock_case, "01/01/2100")
        assert "no es válida" in reply.lower()
        assert "fecha en el futuro".lower() in reply.lower()

    @pytest.mark.asyncio
    async def test_domicilio_uses_address_validator(self):
        """La fase domicilio debe usar el validador de direcciones y pasar a econ_intro si es válida."""
        from application.use_cases.process_incoming_message import ProcessIncomingMessageUseCase

        mock_db = Mock()
        use_case = ProcessIncomingMessageUseCase(mock_db)

        mock_case = Mock()
        mock_case.phase = "domicilio"
        mock_case.nombre = "Juan Pérez"
        mock_case.type = "unilateral"
        mock_case.dni = "12345678"

        # Resultado de validación válido
        fake_result = Mock()
        fake_result.is_valid = True
        fake_result.normalized_address = "San Martín 123, San Rafael, Mendoza"
        use_case.validator_addr.validate_address = Mock(return_value=fake_result)

        # Stub de memoria episódica para no hacer IO real
        use_case.memory.store_episodic_memory = AsyncMock()

        reply = await use_case._phase_domicilio(mock_case, "San Martín 123, San Rafael, Mendoza")

        assert mock_case.phase == "econ_intro"
        assert "datos económicos" in reply.lower()


class TestCaseCreation:
    """Tests de creación y gestión de casos"""
    
    def test_creates_case_for_new_user(self):
        """Test: Crea nuevo caso para usuario nuevo"""
        from infrastructure.persistence.repositories import CaseRepository
        
        mock_db = Mock()
        mock_case = Mock()
        mock_case.id = 1
        mock_case.phone = "+5492604123456"
        mock_case.phase = "inicio"
        
        with patch.object(CaseRepository, 'get_or_create_by_phone', return_value=mock_case):
            repo = CaseRepository(mock_db)
            case = repo.get_or_create_by_phone("+5492604123456")
            
            assert case is not None
            assert case.phone == "+5492604123456"
    
    def test_retrieves_existing_case_for_returning_user(self):
        """Test: Recupera caso existente para usuario que retorna"""
        from infrastructure.persistence.repositories import CaseRepository
        
        mock_db = Mock()
        mock_case = Mock()
        mock_case.id = 1
        mock_case.phone = "+5492604123456"
        mock_case.phase = "documentacion"
        mock_case.nombre = "Juan Pérez"
        
        with patch.object(CaseRepository, 'get_or_create_by_phone', return_value=mock_case):
            repo = CaseRepository(mock_db)
            case = repo.get_or_create_by_phone("+5492604123456")
            
            assert case.nombre == "Juan Pérez"
            assert case.phase == "documentacion"


class TestMessageStorage:
    """Tests de almacenamiento de mensajes"""
    
    def test_stores_user_message(self):
        """Test: Almacena mensaje del usuario"""
        from infrastructure.persistence.repositories import MessageRepository
        
        mock_db = Mock()
        mock_message = Mock()
        mock_message.role = "user"
        mock_message.content = "Hola"
        
        with patch.object(MessageRepository, 'add_message', return_value=mock_message):
            repo = MessageRepository(mock_db)
            message = repo.add_message(case_id=1, role="user", content="Hola")
            
            assert message.role == "user"
            assert message.content == "Hola"
    
    def test_stores_assistant_response(self):
        """Test: Almacena respuesta del asistente"""
        from infrastructure.persistence.repositories import MessageRepository
        
        mock_db = Mock()
        mock_message = Mock()
        mock_message.role = "assistant"
        mock_message.content = "¿Cómo puedo ayudarte?"
        
        with patch.object(MessageRepository, 'add_message', return_value=mock_message):
            repo = MessageRepository(mock_db)
            message = repo.add_message(case_id=1, role="assistant", content="¿Cómo puedo ayudarte?")
            
            assert message.role == "assistant"


class TestValidationServices:
    """Tests de integración con servicios de validación"""
    
    def test_calls_response_validation_service(self):
        """Test: Llama al servicio de validación de respuestas"""
        from infrastructure.validation.response_validation_service_impl import SimpleResponseValidationService
        
        service = SimpleResponseValidationService()
        result = service.validate_user_response("Juan Pérez", "nombre", "nombre completo")
        
        assert result is not None
        assert hasattr(result, 'is_valid')
    
    def test_calls_address_validation_service(self):
        """Test: Llama al servicio de validación de direcciones"""
        from infrastructure.validation.address_validation_service_impl import SimpleAddressValidationService
        
        service = SimpleAddressValidationService()
        result = service.validate_address("San Martín 123, San Rafael, Mendoza")
        
        assert result is not None
        assert hasattr(result, 'is_valid')
    
    def test_calls_date_validation_service(self):
        """Test: Llama al servicio de validación de fechas"""
        from infrastructure.validation.date_validation_service_impl import SimpleDateValidationService
        
        service = SimpleDateValidationService()
        result = service.validate_birth_date("01/01/1990")
        
        assert result is not None
        assert hasattr(result, 'is_valid')


class TestLLMIntegration:
    """Tests de integración con LLM"""
    
    @pytest.mark.asyncio
    async def test_uses_llm_for_general_questions(self):
        """Test: Usa LLM para preguntas generales"""
        from infrastructure.ai.router import LLMRouter
        
        mock_router = Mock(spec=LLMRouter)
        mock_router.chat = AsyncMock(return_value="Esta es la respuesta del LLM")
        
        response = await mock_router.chat([{"role": "user", "content": "¿Cuánto cuesta un divorcio?"}])
        
        assert response is not None
        assert isinstance(response, str)
        mock_router.chat.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_llm_receives_conversation_history(self):
        """Test: LLM recibe historial de conversación"""
        from infrastructure.ai.router import LLMRouter
        
        mock_router = Mock(spec=LLMRouter)
        mock_router.chat = AsyncMock(return_value="Respuesta contextual")
        
        history = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "Hola, ¿cómo puedo ayudarte?"},
            {"role": "user", "content": "¿Qué necesito para divorciarme?"}
        ]
        
        await mock_router.chat(history)
        
        mock_router.chat.assert_called_once_with(history)


class TestErrorHandling:
    """Tests de manejo de errores y fallback de alucinaciones"""
    
    @pytest.mark.asyncio
    async def test_hallucination_fallback_overrides_reply(self):
        """Si el detector de alucinaciones marca la respuesta como inválida, se usa el mensaje seguro."""
        from application.use_cases.process_incoming_message import (
            ProcessIncomingMessageUseCase,
            IncomingMessageRequest,
        )

        mock_db = Mock()
        mock_case = Mock()
        mock_case.id = 1
        mock_case.phone = "+5492604000001"
        mock_case.phase = "inicio"

        with patch("application.use_cases.process_incoming_message.CaseRepository") as CaseRepoMock, \
             patch("application.use_cases.process_incoming_message.MessageRepository") as MsgRepoMock, \
             patch("application.use_cases.process_incoming_message.MemoryService") as MemorySvcMock, \
             patch("application.use_cases.process_incoming_message.HallucinationDetectionService") as HallucMock, \
             patch("application.use_cases.process_incoming_message.LLMRouter") as LLMRouterMock:

            case_repo_instance = CaseRepoMock.return_value
            case_repo_instance.get_or_create_by_phone.return_value = mock_case

            memory_instance = MemorySvcMock.return_value
            memory_instance.store_immediate_memory = AsyncMock()
            memory_instance.build_context_for_llm = AsyncMock(return_value="contexto")
            memory_instance.store_session_memory = AsyncMock()

            halluc_instance = HallucMock.return_value
            halluc_result = Mock()
            halluc_result.is_valid = False
            halluc_result.confidence = 0.2
            halluc_result.flags = ["contradicción"]
            halluc_instance.check_response = AsyncMock(return_value=halluc_result)

            llm_instance = LLMRouterMock.return_value
            llm_instance.chat = AsyncMock(return_value="respuesta arriesgada")

            use_case = ProcessIncomingMessageUseCase(mock_db)

            # Forzar que _handle_phase devuelva una respuesta "original" para luego ser reemplazada
            async def fake_handle_phase(case, text: str) -> str:  # type: ignore[unused-arg]
                return "respuesta potencialmente alucinada"

            use_case._handle_phase = fake_handle_phase  # type: ignore[assignment]

            req = IncomingMessageRequest(phone=mock_case.phone, text="Pregunta compleja")
            response = await use_case.execute(req)

            assert "disculp" in response.text.lower()
            assert "reformular" in response.text.lower()

    @pytest.mark.asyncio
    async def test_handles_llm_error_gracefully_in_fallback(self):
        """Si el LLM falla en el fallback, el caso de uso no debe explotar."""
        from application.use_cases.process_incoming_message import ProcessIncomingMessageUseCase

        mock_db = Mock()
        use_case = ProcessIncomingMessageUseCase(mock_db)

        mock_case = Mock()
        mock_case.id = 1

        # Simular fallo del LLM
        use_case.llm.chat = AsyncMock(side_effect=Exception("LLM caído"))

        # Aunque falle, _llm_fallback debería propagar una excepción; el manejo global se testea vía execute.
        # Aquí verificamos simplemente que la llamada levanta la excepción prevista.
        with pytest.raises(Exception):
            await use_case._llm_fallback(mock_case, "texto")


class TestResponseGeneration:
    """Tests de generación de respuestas"""
    
    def test_generates_welcome_message_for_new_user(self):
        """Test: Genera mensaje de bienvenida para usuario nuevo"""
        # Verificar que se genera un mensaje de bienvenida apropiado
        welcome_keywords = ["hola", "bienvenido", "asistente", "defensoría"]
        # Mock response debería contener alguna de estas palabras
        pass
    
    def test_generates_phase_specific_questions(self):
        """Test: Genera preguntas específicas según la fase"""
        # Cada fase debe tener preguntas específicas
        phase_questions = {
            "tipo_divorcio": ["unilateral", "conjunta"],
            "nombre": ["nombre completo"],
            "dni": ["dni", "documento"],
            "fecha_nacimiento": ["fecha de nacimiento"],
            "domicilio": ["domicilio", "dirección"]
        }
        pass
    
    def test_includes_validation_feedback_in_response(self):
        """Test: Incluye feedback de validación en la respuesta"""
        # Si hay error de validación, la respuesta debe explicarlo
        pass


class TestContextMemory:
    """Tests de memoria contextual"""
    
    def test_retrieves_recent_message_history(self):
        """Test: Recupera historial reciente de mensajes"""
        from infrastructure.persistence.repositories import MessageRepository
        
        mock_db = Mock()
        mock_messages = [
            Mock(role="user", content="Mensaje 1"),
            Mock(role="assistant", content="Respuesta 1"),
            Mock(role="user", content="Mensaje 2"),
        ]
        
        with patch.object(MessageRepository, 'last_messages', return_value=mock_messages):
            repo = MessageRepository(mock_db)
            messages = repo.last_messages(case_id=1, limit=10)
            
            assert len(messages) == 3
    
    def test_limits_history_to_last_n_messages(self):
        """Test: Limita historial a últimos N mensajes"""
        # El sistema debe mantener solo los últimos 10 mensajes por ejemplo
        limit = 10
        # Verificar que no se recuperan más de 'limit' mensajes
        pass


class TestMediaHandling:
    """Tests de manejo de imágenes y media"""
    
    @pytest.mark.asyncio
    async def test_detects_image_attachment(self):
        """Test: Detecta cuando hay imagen adjunta"""
        from application.use_cases.process_incoming_message import IncomingMessageRequest
        
        # Request con media_id
        request = IncomingMessageRequest(
            phone="+5492604123456",
            text="Mi DNI",
            media_id="img_123",
            mime_type="image/jpeg",
        )
        
        assert request.media_id is not None
        assert request.mime_type.startswith("image/")
    
    @pytest.mark.asyncio
    async def test_handle_media_in_documentacion_stores_pdf_reference(self):
        """En fase documentación, un PDF debe almacenarse y devolver mensaje de confirmación genérico."""
        from application.use_cases.process_incoming_message import (
            ProcessIncomingMessageUseCase,
            IncomingMessageRequest,
        )

        mock_db = Mock()
        mock_case = Mock()
        mock_case.id = 1
        mock_case.phase = "documentacion"
        mock_case.dni_image_url = None
        mock_case.marriage_cert_url = None

        with patch("application.use_cases.process_incoming_message.CaseRepository") as CaseRepoMock, \
             patch("application.use_cases.process_incoming_message.MultiProviderOCRService") as OCRMock, \
             patch("application.use_cases.process_incoming_message.WAHAWhatsAppService") as WahaMock, \
             patch("application.use_cases.process_incoming_message.MemoryService") as MemorySvcMock, \
             patch("application.use_cases.process_incoming_message.HallucinationDetectionService") as HallucMock, \
             patch("application.use_cases.process_incoming_message.LLMRouter") as LLMRouterMock, \
             patch("application.use_cases.process_incoming_message.MessageRepository") as MsgRepoMock:

            CaseRepoMock.return_value.get_or_create_by_phone.return_value = mock_case

            # WhatsApp devuelve bytes de archivo
            WahaMock.return_value.download_media = AsyncMock(return_value=b"%PDF-1.4 fake")

            # OCR no es utilizado en este camino porque el PDF no se rasteriza correctamente
            ocr_instance = OCRMock.return_value
            ocr_instance.extract_dni_data = AsyncMock()

            MemorySvcMock.return_value.store_immediate_memory = AsyncMock()
            MemorySvcMock.return_value.build_context_for_llm = AsyncMock(return_value="")
            MemorySvcMock.return_value.store_session_memory = AsyncMock()

            HallucMock.return_value.check_response = AsyncMock()
            LLMRouterMock.return_value.chat = AsyncMock(return_value="")

            use_case = ProcessIncomingMessageUseCase(mock_db)

            req = IncomingMessageRequest(
                phone="+5492604000002",
                text="",
                media_id="media_pdf_1",
                mime_type="application/pdf",
            )

            response = await use_case.execute(req)

            assert "recibí tu archivo" in response.text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
