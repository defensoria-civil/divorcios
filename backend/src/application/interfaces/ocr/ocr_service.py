from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class OCRResult:
    """Resultado de extracción OCR"""
    success: bool
    data: Dict[str, Any]
    confidence: float
    errors: list[str]
    raw_text: Optional[str] = None

class OCRService(ABC):
    @abstractmethod
    async def extract_dni_data(self, image_bytes: bytes) -> OCRResult:
        """
        Extrae datos de un DNI argentino:
        - Número de documento
        - Nombre completo
        - Fecha de nacimiento
        - Sexo
        - Fecha de emisión
        """
        raise NotImplementedError
    
    @abstractmethod
    async def extract_marriage_certificate_data(self, image_bytes: bytes) -> OCRResult:
        """
        Extrae datos de un acta de matrimonio:
        - Fecha de matrimonio
        - Lugar de matrimonio
        - Nombres de los cónyuges
        - Datos del registro civil
        """
        raise NotImplementedError
    
    @abstractmethod
    async def extract_generic_document(self, image_bytes: bytes) -> OCRResult:
        """Extrae texto completo de cualquier documento"""
        raise NotImplementedError
