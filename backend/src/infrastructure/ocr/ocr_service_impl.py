import re
import json
import structlog
from typing import Dict, Any
from application.interfaces.ocr.ocr_service import OCRService, OCRResult
from infrastructure.ai.ollama_vision_client import OllamaVisionClient
from core.config import settings

logger = structlog.get_logger()


class MultiProviderOCRService(OCRService):
    """
    Servicio OCR con múltiples proveedores y fallback automático.
    
    Usa Ollama Vision (qwen3-vl) como proveedor primario y Gemini Vision
    como fallback en caso de fallo.
    
    Responsabilidades:
    - Extracción estructurada de datos de documentos argentinos
    - Validación de datos extraídos según reglas de negocio
    - Fallback automático entre proveedores
    - Logging de proveedor usado y métricas de confianza
    """
    
    def __init__(self):
        self.vision_client = OllamaVisionClient()
        self.gemini_fallback_enabled = bool(settings.gemini_api_key)
        
        if self.gemini_fallback_enabled:
            # Import lazy para no fallar si Gemini no está configurado
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    
    def _parse_json_response(self, raw_text: str) -> Dict[str, Any]:
        """
        Extrae y parsea JSON de la respuesta del modelo.
        
        Args:
            raw_text: Respuesta cruda del modelo
            
        Returns:
            Diccionario con datos parseados
            
        Raises:
            json.JSONDecodeError: Si no se puede parsear el JSON
        """
        # Limpiar markdown si existe
        json_text = raw_text.replace("```json", "").replace("```", "").strip()
        return json.loads(json_text)
    
    def _validate_dni_data(self, data: Dict[str, Any]) -> tuple[list[str], float]:
        """
        Valida datos extraídos de DNI.
        
        Returns:
            Tupla de (errores, confidence)
        """
        errors = []
        confidence = 0.9
        
        # Validar número de documento
        if not data.get("numero_documento") or not re.match(
            r"^\d{7,8}$", 
            str(data.get("numero_documento", ""))
        ):
            errors.append("Número de documento no válido o no detectado")
            confidence -= 0.3
        
        # Validar nombre completo
        if not data.get("nombre_completo"):
            errors.append("Nombre completo no detectado")
            confidence -= 0.2
        
        # Validar fecha de nacimiento
        if not data.get("fecha_nacimiento") or not re.match(
            r"^\d{2}/\d{2}/\d{4}$",
            str(data.get("fecha_nacimiento", ""))
        ):
            errors.append("Fecha de nacimiento no válida")
            confidence -= 0.2
        
        return errors, max(0.0, confidence)
    
    def _validate_marriage_data(self, data: Dict[str, Any]) -> tuple[list[str], float]:
        """
        Valida datos extraídos de acta de matrimonio.
        
        Returns:
            Tupla de (errores, confidence)
        """
        errors = []
        confidence = 0.9
        
        # Validar fecha de matrimonio
        if not data.get("fecha_matrimonio") or not re.match(
            r"^\d{2}/\d{2}/\d{4}$",
            str(data.get("fecha_matrimonio", ""))
        ):
            errors.append("Fecha de matrimonio no válida")
            confidence -= 0.4
        
        # Validar nombres de cónyuges
        if not data.get("nombre_conyuge_1") or not data.get("nombre_conyuge_2"):
            errors.append("Nombres de cónyuges incompletos")
            confidence -= 0.4
        
        # Validar lugar
        if not data.get("lugar_matrimonio"):
            errors.append("Lugar de matrimonio no detectado")
            confidence -= 0.1
        
        return errors, max(0.0, confidence)

    def _validate_anses_data(self, data: Dict[str, Any]) -> tuple[list[str], float]:
        """Valida datos de certificación negativa de ANSES."""
        errors = []
        confidence = 0.9
        
        if not data.get("cuil"):
            errors.append("CUIL no detectado")
            confidence -= 0.3
            
        if not data.get("periodo"):
            errors.append("Periodo no detectado")
            confidence -= 0.2
            
        if data.get("es_negativa") is None:
            errors.append("No se pudo determinar si es negativa")
            confidence -= 0.2
            
        return errors, max(0.0, confidence)

    async def extract_dni_data(self, image_bytes: bytes) -> OCRResult:
        """
        Extrae datos estructurados de un DNI argentino.
        
        Args:
            image_bytes: Bytes de la imagen del DNI
            
        Returns:
            OCRResult con datos extraídos y validados
        """
        prompt = """Eres un experto en extraer datos de documentos argentinos.
Analiza esta imagen de DNI argentino y extrae EXACTAMENTE los siguientes datos en formato JSON:

{
  "numero_documento": "string con 7-8 dígitos",
  "nombre_completo": "string con nombre y apellido",
  "fecha_nacimiento": "DD/MM/AAAA",
  "sexo": "M o F",
  "fecha_emision": "DD/MM/AAAA"
}

Reglas importantes:
- Si algún dato NO está visible o legible, usa null
- Formato de fechas SIEMPRE DD/MM/AAAA
- Número de documento sin puntos ni espacios
- Nombre completo en MAYÚSCULAS como aparece en el DNI

Responde SOLO con el JSON, sin explicaciones adicionales."""
        
        # Intentar con Ollama Vision primero
        try:
            logger.info("dni_ocr_attempt", provider="ollama_vision")
            
            # Usar modelo de visión cloud explícitamente
            raw_text = await self.vision_client.analyze_image(
                image_bytes, 
                prompt, 
                model=settings.llm_vision_model
            )
            data = self._parse_json_response(raw_text)
            errors, confidence = self._validate_dni_data(data)
            success = len(errors) == 0 or confidence > 0.5
            
            logger.info(
                "dni_ocr_success",
                provider="ollama_vision",
                confidence=confidence,
                success=success
            )
            
            return OCRResult(
                success=success,
                data=data,
                confidence=confidence,
                errors=errors,
                raw_text=raw_text
            )
            
        except Exception as e:
            logger.warning("dni_ocr_ollama_failed", error=str(e))
            
            # Fallback a Gemini si está disponible
            if self.gemini_fallback_enabled:
                return await self._extract_dni_gemini_fallback(image_bytes, prompt)
            else:
                logger.error("dni_ocr_failed_no_fallback", error=str(e))
                return OCRResult(
                    success=False,
                    data={},
                    confidence=0.0,
                    errors=[f"Error en procesamiento OCR: {str(e)}"],
                    raw_text=None
                )
    
    async def _extract_dni_gemini_fallback(
        self,
        image_bytes: bytes,
        prompt: str
    ) -> OCRResult:
        """Fallback a Gemini Vision para extracción de DNI"""
        try:
            from PIL import Image
            from io import BytesIO
            
            logger.info("dni_ocr_attempt", provider="gemini_vision")
            
            image = Image.open(BytesIO(image_bytes))
            response = await self.gemini_model.generate_content_async([prompt, image])
            raw_text = response.text.strip()
            
            data = self._parse_json_response(raw_text)
            errors, confidence = self._validate_dni_data(data)
            success = len(errors) == 0 or confidence > 0.5
            
            logger.info(
                "dni_ocr_success",
                provider="gemini_vision",
                confidence=confidence,
                success=success
            )
            
            return OCRResult(
                success=success,
                data=data,
                confidence=confidence,
                errors=errors,
                raw_text=raw_text
            )
            
        except Exception as e:
            logger.error("dni_ocr_gemini_failed", error=str(e))
            return OCRResult(
                success=False,
                data={},
                confidence=0.0,
                errors=[f"Error en procesamiento OCR (todos los proveedores): {str(e)}"],
                raw_text=None
            )

    async def extract_anses_data(self, image_bytes: bytes) -> OCRResult:
        """
        Extrae datos de una Certificación Negativa de ANSES.
        """
        prompt = """Eres un experto en documentos administrativos argentinos.
Analiza esta imagen de CERTIFICACIÓN NEGATIVA DE ANSES y extrae los siguientes datos en JSON:

{
  "cuil": "string (formato XX-XXXXXXXX-X)",
  "periodo": "string (ej: Noviembre 2025)",
  "es_negativa": boolean (true si dice "NO REGISTRA" declaraciones juradas/aportes, false si registra algo),
  "fecha_emision": "DD/MM/AAAA"
}

Reglas:
- Busca el texto "NO REGISTRA" para determinar si es negativa.
- Si dice "REGISTRA", es_negativa = false.
- Extrae el CUIL del titular.

Responde SOLO con el JSON."""

        try:
            logger.info("anses_ocr_attempt", provider="ollama_vision")
            raw_text = await self.vision_client.analyze_image(
                image_bytes, prompt, model=settings.llm_vision_model
            )
            data = self._parse_json_response(raw_text)
            errors, confidence = self._validate_anses_data(data)
            success = len(errors) == 0 or confidence > 0.6
            
            return OCRResult(success=success, data=data, confidence=confidence, errors=errors, raw_text=raw_text)
        except Exception as e:
            logger.warning("anses_ocr_ollama_failed", error=str(e))
            if self.gemini_fallback_enabled:
                return await self._extract_anses_gemini_fallback(image_bytes, prompt)
            return OCRResult(success=False, data={}, confidence=0.0, errors=[str(e)], raw_text=None)

    async def _extract_anses_gemini_fallback(self, image_bytes: bytes, prompt: str) -> OCRResult:
        try:
            from PIL import Image
            from io import BytesIO
            image = Image.open(BytesIO(image_bytes))
            response = await self.gemini_model.generate_content_async([prompt, image])
            raw_text = response.text.strip()
            data = self._parse_json_response(raw_text)
            errors, confidence = self._validate_anses_data(data)
            success = len(errors) == 0 or confidence > 0.6
            return OCRResult(success=success, data=data, confidence=confidence, errors=errors, raw_text=raw_text)
        except Exception as e:
            return OCRResult(success=False, data={}, confidence=0.0, errors=[str(e)], raw_text=None)
    
    async def extract_marriage_certificate_data(self, image_bytes: bytes) -> OCRResult:
        """
        Extrae datos de un acta de matrimonio argentina.
        
        Args:
            image_bytes: Bytes de la imagen del acta
            
        Returns:
            OCRResult con datos extraídos y validados
        """
        prompt = """Eres un experto en extraer datos de documentos legales argentinos.
Analiza esta imagen de ACTA DE MATRIMONIO argentina y extrae EXACTAMENTE los siguientes datos en formato JSON:

{
  "fecha_matrimonio": "DD/MM/AAAA",
  "lugar_matrimonio": "string (ciudad, provincia)",
  "nombre_conyuge_1": "string",
  "nombre_conyuge_2": "string",
  "registro_civil": "string",
  "numero_acta": "string",
  "tomo": "string",
  "folio": "string"
}

Reglas importantes:
- Si algún dato NO está visible o legible, usa null
- Formato de fechas SIEMPRE DD/MM/AAAA
- Nombres completos como aparecen en el acta
- Incluye todos los datos del registro civil que encuentres

Responde SOLO con el JSON, sin explicaciones adicionales."""
        
        # Intentar con Ollama Vision primero
        try:
            logger.info("marriage_cert_ocr_attempt", provider="ollama_vision")
            
            # Usar modelo de visión cloud explícitamente
            raw_text = await self.vision_client.analyze_image(
                image_bytes, 
                prompt, 
                model=settings.llm_vision_model
            )
            data = self._parse_json_response(raw_text)
            errors, confidence = self._validate_marriage_data(data)
            success = len(errors) == 0 or confidence > 0.7
            
            logger.info(
                "marriage_cert_ocr_success",
                provider="ollama_vision",
                confidence=confidence,
                success=success
            )
            
            return OCRResult(
                success=success,
                data=data,
                confidence=confidence,
                errors=errors,
                raw_text=raw_text
            )
            
        except Exception as e:
            logger.warning("marriage_cert_ocr_ollama_failed", error=str(e))
            
            # Fallback a Gemini si está disponible
            if self.gemini_fallback_enabled:
                return await self._extract_marriage_gemini_fallback(image_bytes, prompt)
            else:
                logger.error("marriage_cert_ocr_failed_no_fallback", error=str(e))
                return OCRResult(
                    success=False,
                    data={},
                    confidence=0.0,
                    errors=[f"Error en procesamiento OCR: {str(e)}"],
                    raw_text=None
                )
    
    async def _extract_marriage_gemini_fallback(
        self,
        image_bytes: bytes,
        prompt: str
    ) -> OCRResult:
        """Fallback a Gemini Vision para extracción de acta matrimonial"""
        try:
            from PIL import Image
            from io import BytesIO
            
            logger.info("marriage_cert_ocr_attempt", provider="gemini_vision")
            
            image = Image.open(BytesIO(image_bytes))
            response = await self.gemini_model.generate_content_async([prompt, image])
            raw_text = response.text.strip()
            
            data = self._parse_json_response(raw_text)
            errors, confidence = self._validate_marriage_data(data)
            success = len(errors) == 0 or confidence > 0.5
            
            logger.info(
                "marriage_cert_ocr_success",
                provider="gemini_vision",
                confidence=confidence,
                success=success
            )
            
            return OCRResult(
                success=success,
                data=data,
                confidence=confidence,
                errors=errors,
                raw_text=raw_text
            )
            
        except Exception as e:
            logger.error("marriage_cert_ocr_gemini_failed", error=str(e))
            return OCRResult(
                success=False,
                data={},
                confidence=0.0,
                errors=[f"Error en procesamiento OCR (todos los proveedores): {str(e)}"],
                raw_text=None
            )
    
    async def extract_generic_document(self, image_bytes: bytes) -> OCRResult:
        """
        Extrae texto completo de cualquier documento.
        
        Args:
            image_bytes: Bytes de la imagen del documento
            
        Returns:
            OCRResult con texto extraído
        """
        prompt = "Extrae TODO el texto visible en esta imagen de documento. Responde solo con el texto extraído, manteniendo el formato original lo más posible."
        
        try:
            logger.info("generic_ocr_attempt", provider="ollama_vision")
            
            # Usar modelo de visión cloud explícitamente
            raw_text = await self.vision_client.analyze_image(
                image_bytes, 
                prompt, 
                model=settings.llm_vision_model
            )
            
            logger.info(
                "generic_ocr_success",
                provider="ollama_vision",
                text_length=len(raw_text)
            )
            
            return OCRResult(
                success=bool(raw_text),
                data={"text": raw_text},
                confidence=0.8 if raw_text else 0.0,
                errors=[] if raw_text else ["No se pudo extraer texto del documento"],
                raw_text=raw_text
            )
            
        except Exception as e:
            logger.warning("generic_ocr_ollama_failed", error=str(e))
            
            # Fallback a Gemini
            if self.gemini_fallback_enabled:
                return await self._extract_generic_gemini_fallback(image_bytes, prompt)
            else:
                logger.error("generic_ocr_failed_no_fallback", error=str(e))
                return OCRResult(
                    success=False,
                    data={},
                    confidence=0.0,
                    errors=[f"Error en procesamiento OCR: {str(e)}"],
                    raw_text=None
                )
    
    async def _extract_generic_gemini_fallback(
        self,
        image_bytes: bytes,
        prompt: str
    ) -> OCRResult:
        """Fallback a Gemini Vision para OCR genérico"""
        try:
            from PIL import Image
            from io import BytesIO
            
            logger.info("generic_ocr_attempt", provider="gemini_vision")
            
            image = Image.open(BytesIO(image_bytes))
            response = await self.gemini_model.generate_content_async([prompt, image])
            raw_text = response.text.strip()
            
            logger.info(
                "generic_ocr_success",
                provider="gemini_vision",
                text_length=len(raw_text)
            )
            
            return OCRResult(
                success=bool(raw_text),
                data={"text": raw_text},
                confidence=0.8 if raw_text else 0.0,
                errors=[] if raw_text else ["No se pudo extraer texto del documento"],
                raw_text=raw_text
            )
            
        except Exception as e:
            logger.error("generic_ocr_gemini_failed", error=str(e))
            return OCRResult(
                success=False,
                data={},
                confidence=0.0,
                errors=[f"Error en procesamiento OCR (todos los proveedores): {str(e)}"],
                raw_text=None
            )
