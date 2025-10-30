import re
import structlog
import google.generativeai as genai
from typing import Dict, Any
from application.interfaces.ocr.ocr_service import OCRService, OCRResult
from core.config import settings

logger = structlog.get_logger()

class GeminiOCRService(OCRService):
    """Servicio OCR usando Gemini Vision para extracción inteligente de datos"""
    
    def __init__(self):
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
        self.vision_model = genai.GenerativeModel("gemini-1.5-flash")
    
    async def extract_dni_data(self, image_bytes: bytes) -> OCRResult:
        """Extrae datos estructurados de un DNI argentino usando Gemini Vision"""
        
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

        try:
            # Preparar imagen para Gemini
            import base64
            from PIL import Image
            from io import BytesIO
            
            # Convertir bytes a imagen PIL
            image = Image.open(BytesIO(image_bytes))
            
            # Generar contenido con visión
            response = await self.vision_model.generate_content_async([prompt, image])
            raw_text = response.text.strip()
            
            # Extraer JSON de la respuesta
            import json
            # Limpiar markdown si existe
            json_text = raw_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(json_text)
            
            # Validar datos extraídos
            errors = []
            confidence = 0.9  # Base confidence
            
            if not data.get("numero_documento") or not re.match(r"^\d{7,8}$", str(data.get("numero_documento", ""))):
                errors.append("Número de documento no válido o no detectado")
                confidence -= 0.3
            
            if not data.get("nombre_completo"):
                errors.append("Nombre completo no detectado")
                confidence -= 0.2
            
            if not data.get("fecha_nacimiento") or not re.match(r"^\d{2}/\d{2}/\d{4}$", str(data.get("fecha_nacimiento", ""))):
                errors.append("Fecha de nacimiento no válida")
                confidence -= 0.2
            
            success = len(errors) == 0 or confidence > 0.5
            
            logger.info("dni_ocr_completed", success=success, confidence=confidence, errors=errors)
            
            return OCRResult(
                success=success,
                data=data,
                confidence=max(0.0, confidence),
                errors=errors,
                raw_text=raw_text
            )
            
        except Exception as e:
            logger.error("dni_ocr_error", error=str(e))
            return OCRResult(
                success=False,
                data={},
                confidence=0.0,
                errors=[f"Error en procesamiento OCR: {str(e)}"],
                raw_text=None
            )
    
    async def extract_marriage_certificate_data(self, image_bytes: bytes) -> OCRResult:
        """Extrae datos de un acta de matrimonio usando Gemini Vision"""
        
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

        try:
            import base64
            from PIL import Image
            from io import BytesIO
            import json
            
            image = Image.open(BytesIO(image_bytes))
            response = await self.vision_model.generate_content_async([prompt, image])
            raw_text = response.text.strip()
            
            json_text = raw_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(json_text)
            
            errors = []
            confidence = 0.9
            
            if not data.get("fecha_matrimonio") or not re.match(r"^\d{2}/\d{2}/\d{4}$", str(data.get("fecha_matrimonio", ""))):
                errors.append("Fecha de matrimonio no válida")
                confidence -= 0.3
            
            if not data.get("nombre_conyuge_1") or not data.get("nombre_conyuge_2"):
                errors.append("Nombres de cónyuges incompletos")
                confidence -= 0.3
            
            if not data.get("lugar_matrimonio"):
                errors.append("Lugar de matrimonio no detectado")
                confidence -= 0.2
            
            success = len(errors) == 0 or confidence > 0.5
            
            logger.info("marriage_cert_ocr_completed", success=success, confidence=confidence, errors=errors)
            
            return OCRResult(
                success=success,
                data=data,
                confidence=max(0.0, confidence),
                errors=errors,
                raw_text=raw_text
            )
            
        except Exception as e:
            logger.error("marriage_cert_ocr_error", error=str(e))
            return OCRResult(
                success=False,
                data={},
                confidence=0.0,
                errors=[f"Error en procesamiento OCR: {str(e)}"],
                raw_text=None
            )
    
    async def extract_generic_document(self, image_bytes: bytes) -> OCRResult:
        """Extrae texto completo de cualquier documento"""
        
        prompt = "Extrae TODO el texto visible en esta imagen de documento. Responde solo con el texto extraído, manteniendo el formato original lo más posible."
        
        try:
            from PIL import Image
            from io import BytesIO
            
            image = Image.open(BytesIO(image_bytes))
            response = await self.vision_model.generate_content_async([prompt, image])
            raw_text = response.text.strip()
            
            logger.info("generic_ocr_completed", text_length=len(raw_text))
            
            return OCRResult(
                success=bool(raw_text),
                data={"text": raw_text},
                confidence=0.8 if raw_text else 0.0,
                errors=[] if raw_text else ["No se pudo extraer texto del documento"],
                raw_text=raw_text
            )
            
        except Exception as e:
            logger.error("generic_ocr_error", error=str(e))
            return OCRResult(
                success=False,
                data={},
                confidence=0.0,
                errors=[f"Error en procesamiento OCR: {str(e)}"],
                raw_text=None
            )
