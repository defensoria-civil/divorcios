"""
Tests unitarios para procesamiento de imágenes (DNI y actas de matrimonio)
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import date
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from application.use_cases.process_incoming_message import (
    ProcessIncomingMessageUseCase,
    IncomingMessageRequest,
    MessageResponse
)
from application.interfaces.ocr.ocr_service import OCRResult


class TestImageProcessing:
    """Tests para el procesamiento de imágenes en el use case"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock de sesión de base de datos"""
        return Mock()
    
    @pytest.fixture
    def mock_case(self):
        """Mock de caso"""
        case = Mock()
        case.id = 1
        case.phone = "5492604123456"
        case.phase = "documentacion"
        case.dni = None
        case.nombre = None
        case.fecha_nacimiento = None
        case.dni_image_url = None
        case.marriage_cert_url = None
        case.fecha_matrimonio = None
        case.lugar_matrimonio = None
        return case
    
    @pytest.fixture
    def use_case(self, mock_db):
        """Instancia del use case con mocks"""
        with patch('application.use_cases.process_incoming_message.CaseRepository'), \
             patch('application.use_cases.process_incoming_message.MessageRepository'), \
             patch('application.use_cases.process_incoming_message.LLMRouter'), \
             patch('application.use_cases.process_incoming_message.MemoryService'), \
             patch('application.use_cases.process_incoming_message.HallucinationDetectionService'), \
             patch('application.use_cases.process_incoming_message.MultiProviderOCRService'), \
             patch('application.use_cases.process_incoming_message.WAHAWhatsAppService'):

            uc = ProcessIncomingMessageUseCase(mock_db)
            return uc
    
    @pytest.mark.asyncio
    async def test_handle_media_downloads_image(self, use_case, mock_case):
        """Test: _handle_media descarga imagen correctamente"""
        # Arrange
        media_id = "abc123"
        image_bytes = b"fake_image_data"
        
        use_case.whatsapp.download_media = AsyncMock(return_value=image_bytes)
        use_case._process_dni_image = AsyncMock(return_value=MessageResponse(text="OK"))
        use_case.memory.store_session_memory = AsyncMock()
        # Hacer que el OCR detecte un DNI válido para ir directo a _process_dni_image
        ocr_result = OCRResult(
            success=True,
            data={"numero_documento": "12345678"},
            confidence=0.9,
            errors=[],
        )
        use_case.ocr.extract_dni_data = AsyncMock(return_value=ocr_result)
        
        # Act
        result = await use_case._handle_media(mock_case, media_id, None, None)
        
        # Assert
        use_case.whatsapp.download_media.assert_called_once_with(media_id)
        assert result.text == "OK"
    
    @pytest.mark.asyncio
    async def test_handle_media_chooses_dni_when_no_dni_image(self, use_case, mock_case):
        """Test: _handle_media elige procesar DNI cuando no hay dni_image_url"""
        # Arrange
        mock_case.phase = "documentacion"
        mock_case.dni_image_url = None
        
        use_case.whatsapp.download_media = AsyncMock(return_value=b"image")
        use_case._process_dni_image = AsyncMock(return_value=MessageResponse(text="DNI procesado"))
        use_case._process_marriage_cert_image = AsyncMock()
        # Simular que el OCR detecta DNI válido
        ocr_result = OCRResult(
            success=True,
            data={"numero_documento": "12345678"},
            confidence=0.9,
            errors=[],
        )
        use_case.ocr.extract_dni_data = AsyncMock(return_value=ocr_result)
        
        # Act
        await use_case._handle_media(mock_case, "media123", None, None)
        
        # Assert
        use_case._process_dni_image.assert_called_once()
        use_case._process_marriage_cert_image.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_media_chooses_marriage_cert_when_has_dni(self, use_case, mock_case):
        """Test: _handle_media elige procesar acta cuando ya tiene DNI"""
        # Arrange
        mock_case.phase = "documentacion"
        mock_case.dni_image_url = "existing_dni_media_id"
        
        use_case.whatsapp.download_media = AsyncMock(return_value=b"image")
        use_case._process_dni_image = AsyncMock()
        use_case._process_marriage_cert_image = AsyncMock(return_value=MessageResponse(text="Acta procesada"))
        # Simular que el OCR NO detecta DNI pero sí acta de matrimonio
        dni_result = OCRResult(
            success=False,
            data={},
            confidence=0.2,
            errors=["No parece un DNI"],
        )
        cert_result = OCRResult(
            success=True,
            data={},
            confidence=0.9,
            errors=[],
        )
        use_case.ocr.extract_dni_data = AsyncMock(return_value=dni_result)
        use_case.ocr.extract_marriage_certificate_data = AsyncMock(return_value=cert_result)
        
        # Act
        await use_case._handle_media(mock_case, "media456", None, None)
        
        # Assert
        use_case._process_marriage_cert_image.assert_called_once()
        use_case._process_dni_image.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_media_rejects_image_in_wrong_phase(self, use_case, mock_case):
        """Test: _handle_media rechaza imagen en fase incorrecta"""
        # Arrange
        mock_case.phase = "inicio"  # Fase que no acepta imágenes
        
        use_case.whatsapp.download_media = AsyncMock(return_value=b"image")
        
        # Act
        result = await use_case._handle_media(mock_case, "media789", None, None)
        
        # Assert
        assert "todavía no estamos en la etapa de documentación" in result.text
    
    @pytest.mark.asyncio
    async def test_process_dni_image_success(self, use_case, mock_case):
        """Test: _process_dni_image procesa DNI exitosamente"""
        # Arrange
        image_bytes = b"dni_image"
        media_id = "dni123"
        
        ocr_result = OCRResult(
            success=True,
            data={
                "numero_documento": "12345678",
                "nombre_completo": "JUAN PEREZ",
                "fecha_nacimiento": "01/01/1990"
            },
            confidence=0.9,
            errors=[]
        )
        
        use_case.ocr.extract_dni_data = AsyncMock(return_value=ocr_result)
        use_case.cases.update = Mock()
        use_case.memory.store_immediate_memory = AsyncMock()
        
        # Act
        result = await use_case._process_dni_image(mock_case, image_bytes, media_id)
        
        # Assert
        assert "DNI procesado correctamente" in result.text
        assert "12345678" in result.text
        assert "JUAN PEREZ" in result.text
        assert mock_case.dni == "12345678"
        assert mock_case.nombre == "JUAN PEREZ"
        assert mock_case.dni_image_url == media_id
        use_case.cases.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_dni_image_low_confidence(self, use_case, mock_case):
        """Test: _process_dni_image rechaza DNI con baja confianza"""
        # Arrange
        image_bytes = b"blurry_dni_image"
        media_id = "dni456"
        
        ocr_result = OCRResult(
            success=False,
            data={},
            confidence=0.3,
            errors=["Imagen poco clara", "Número de documento no detectado"]
        )
        
        use_case.ocr.extract_dni_data = AsyncMock(return_value=ocr_result)
        
        # Act
        result = await use_case._process_dni_image(mock_case, image_bytes, media_id)
        
        # Assert
        assert "No pude procesar el DNI correctamente" in result.text
        assert "foto más clara" in result.text
    
    @pytest.mark.asyncio
    async def test_process_marriage_cert_success(self, use_case, mock_case):
        """Test: _process_marriage_cert_image procesa acta exitosamente"""
        # Arrange
        image_bytes = b"marriage_cert_image"
        media_id = "cert123"
        
        ocr_result = OCRResult(
            success=True,
            data={
                "fecha_matrimonio": "15/06/2018",
                "lugar_matrimonio": "San Rafael, Mendoza",
                "nombre_conyuge_1": "JUAN PEREZ",
                "nombre_conyuge_2": "MARIA GOMEZ"
            },
            confidence=0.85,
            errors=[]
        )
        
        use_case.ocr.extract_marriage_certificate_data = AsyncMock(return_value=ocr_result)
        use_case.cases.update = Mock()
        use_case.memory.store_immediate_memory = AsyncMock()
        use_case.memory.store_episodic_memory = AsyncMock()
        
        # Act
        result = await use_case._process_marriage_cert_image(mock_case, image_bytes, media_id)
        
        # Assert
        assert "Acta de matrimonio procesada correctamente" in result.text
        assert "15/06/2018" in result.text
        assert "San Rafael, Mendoza" in result.text
        # El mensaje puede indicar que la documentación está completa,
        # pero el estado del caso puede depender de documentos adicionales.
        assert mock_case.lugar_matrimonio == "San Rafael, Mendoza"
        assert mock_case.marriage_cert_url == media_id
        use_case.cases.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_marriage_cert_low_confidence(self, use_case, mock_case):
        """Test: _process_marriage_cert_image rechaza acta con baja confianza"""
        # Arrange
        image_bytes = b"blurry_cert_image"
        media_id = "cert456"
        
        ocr_result = OCRResult(
            success=False,
            data={},
            confidence=0.4,
            errors=["Fecha de matrimonio no válida", "Lugar no detectado"]
        )
        
        use_case.ocr.extract_marriage_certificate_data = AsyncMock(return_value=ocr_result)
        
        # Act
        result = await use_case._process_marriage_cert_image(mock_case, image_bytes, media_id)
        
        # Assert
        assert "No pude procesar el acta de matrimonio correctamente" in result.text
        assert "foto más clara" in result.text
    
    @pytest.mark.asyncio
    async def test_execute_with_media_id_triggers_image_processing(self, use_case, mock_case):
        """Test: execute() detecta media_id y llama a _handle_media"""
        # Arrange
        request = IncomingMessageRequest(
            phone="5492604123456",
            text="",
            media_id="media123"
        )
        
        use_case.cases.get_or_create_by_phone = Mock(return_value=mock_case)
        use_case._handle_media = AsyncMock(return_value=MessageResponse(text="Imagen procesada"))
        
        # Act
        result = await use_case.execute(request)
        
        # Assert
        use_case._handle_media.assert_called_once_with(mock_case, "media123", None, "")
        assert result.text == "Imagen procesada"
    
    @pytest.mark.asyncio
    async def test_dni_image_advances_phase(self, use_case, mock_case):
        """Test: Procesar DNI en fase 'dni' avanza a fase 'fecha_nacimiento'"""
        # Arrange
        mock_case.phase = "dni"
        image_bytes = b"dni_image"
        media_id = "dni789"
        
        ocr_result = OCRResult(
            success=True,
            data={"numero_documento": "12345678", "nombre_completo": "JUAN PEREZ"},
            confidence=0.8,
            errors=[]
        )
        
        use_case.ocr.extract_dni_data = AsyncMock(return_value=ocr_result)
        use_case.cases.update = Mock()
        use_case.memory.store_immediate_memory = AsyncMock()
        
        # Act
        await use_case._process_dni_image(mock_case, image_bytes, media_id)
        
        # Assert
        assert mock_case.phase == "fecha_nacimiento"


class TestMigrationScript:
    """Tests para el script de migración"""
    
    def test_migration_script_syntax(self):
        """Test: Script de migración tiene sintaxis correcta"""
        import subprocess
        from pathlib import Path
        
        # Encontrar el script desde la raíz del proyecto
        script_path = Path(__file__).parent.parent.parent / "scripts" / "migrate_add_document_fields.py"
        
        result = subprocess.run(
            ["python", "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Syntax error in migration script: {result.stderr}"


class TestModels:
    """Tests para el modelo Case"""
    
    def test_case_model_has_new_fields(self):
        """Test: Modelo Case tiene los campos nuevos"""
        from infrastructure.persistence.models import Case
        
        # Verificar que los campos existen
        assert hasattr(Case, 'dni_image_url')
        assert hasattr(Case, 'marriage_cert_url')
        assert hasattr(Case, 'fecha_matrimonio')
        assert hasattr(Case, 'lugar_matrimonio')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
