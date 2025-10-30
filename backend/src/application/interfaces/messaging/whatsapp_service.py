from abc import ABC, abstractmethod
from typing import Optional, BinaryIO

class WhatsAppService(ABC):
    @abstractmethod
    async def send_message(self, phone: str, message: str) -> dict:
        """Envía un mensaje de texto a un número de WhatsApp"""
        raise NotImplementedError
    
    @abstractmethod
    async def send_document(self, phone: str, file_content: bytes, filename: str, caption: Optional[str] = None) -> dict:
        """Envía un documento (PDF, JPG, PNG) a un número de WhatsApp"""
        raise NotImplementedError
    
    @abstractmethod
    async def download_media(self, media_id: str) -> bytes:
        """Descarga un archivo multimedia enviado por el usuario"""
        raise NotImplementedError
