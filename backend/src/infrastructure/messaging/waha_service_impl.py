import httpx
import structlog
from typing import Optional
from application.interfaces.messaging.whatsapp_service import WhatsAppService
from core.config import settings

logger = structlog.get_logger()

class WAHAWhatsAppService(WhatsAppService):
    """Implementación del servicio de WhatsApp usando WAHA HTTP API"""
    
    def __init__(self):
        self.base_url = settings.waha_base_url.rstrip("/")
        self.api_key = settings.waha_api_key
        self.session_name = "default"  # Configurable si se necesita múltiples sesiones
    
    def _headers(self) -> dict:
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def send_message(self, phone_or_chat: str, message: str) -> dict:
        """Envía un mensaje de texto. Acepta MSISDN o JID (chatId)."""
        raw = phone_or_chat.strip()
        # Determinar chatId y phone según formato recibido
        if "@" in raw:
            chat_id = raw  # ya viene como JID (p.ej. 549xxxxxxxxx@c.us o 261...@lid)
            msisdn = raw.split("@")[0]
        else:
            msisdn = raw.lstrip("+")
            if not msisdn.startswith("549"):
                msisdn = f"549{msisdn}"
            chat_id = f"{msisdn}@c.us"
        
        url = f"{self.base_url}/api/sendText"
        payload = {
            "session": self.session_name,
            "chatId": chat_id,
            "text": message
        }
        
        try:
            async with httpx.AsyncClient(timeout=30, verify=False) as client:
                response = await client.post(url, json=payload, headers=self._headers())
                if response.status_code >= 400:
                    body = response.text
                    logger.warning("whatsapp_send_primary_failed", status=response.status_code, body=body)
                    # Fallback: usar parámetro 'phone' en lugar de 'chatId'
                    alt_payload = {"session": self.session_name, "phone": msisdn, "text": message}
                    alt_resp = await client.post(url, json=alt_payload, headers=self._headers())
                    alt_resp.raise_for_status()
                    result = alt_resp.json()
                    logger.info("whatsapp_message_sent_fallback_phone", phone=msisdn, chat_id=chat_id, result=result)
                    return result
                response.raise_for_status()
                result = response.json()
                logger.info("whatsapp_message_sent", phone=msisdn, chat_id=chat_id, result=result)
                return result
        except Exception as e:
            logger.error("whatsapp_send_error", phone=msisdn, chat_id=chat_id, error=str(e))
            raise
    
    async def send_document(self, phone_or_chat: str, file_content: bytes, filename: str, caption: Optional[str] = None) -> dict:
        """Envía un documento (PDF, JPG, PNG). Acepta MSISDN o JID (chatId)."""
        raw = phone_or_chat.strip()
        if "@" in raw:
            chat_id = raw
            msisdn = raw.split("@")[0]
        else:
            msisdn = raw.lstrip("+")
            if not msisdn.startswith("549"):
                msisdn = f"549{msisdn}"
            chat_id = f"{msisdn}@c.us"
        
        url = f"{self.base_url}/api/sendFile"
        
        # WAHA acepta archivos en base64 o como URL
        import base64
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        payload = {
            "session": self.session_name,
            "chatId": chat_id,
            "file": {
                "mimetype": self._get_mimetype(filename),
                "filename": filename,
                "data": file_base64
            },
            "caption": caption or ""
        }
        
        try:
            async with httpx.AsyncClient(timeout=60, verify=False) as client:
                response = await client.post(url, json=payload, headers=self._headers())
                if response.status_code >= 400:
                    body = response.text
                    logger.warning("whatsapp_send_file_primary_failed", status=response.status_code, body=body)
                    # Fallback: usar 'phone' en lugar de 'chatId'
                    alt_payload = dict(payload)
                    alt_payload.pop("chatId", None)
                    alt_payload["phone"] = msisdn
                    alt_resp = await client.post(url, json=alt_payload, headers=self._headers())
                    alt_resp.raise_for_status()
                    result = alt_resp.json()
                    logger.info("whatsapp_document_sent_fallback_phone", phone=msisdn, chat_id=chat_id, filename=filename, result=result)
                    return result
                response.raise_for_status()
                result = response.json()
                logger.info("whatsapp_document_sent", phone=msisdn, chat_id=chat_id, filename=filename, result=result)
                return result
        except Exception as e:
            logger.error("whatsapp_send_document_error", phone=msisdn, chat_id=chat_id, filename=filename, error=str(e))
            raise
    
    async def download_media(self, media_id: str) -> bytes:
        """Descarga un archivo multimedia enviado por el usuario"""
        url = f"{self.base_url}/api/files/{media_id}"
        
        try:
            async with httpx.AsyncClient(timeout=60, verify=False) as client:
                response = await client.get(url, headers=self._headers())
                response.raise_for_status()
                logger.info("whatsapp_media_downloaded", media_id=media_id, size=len(response.content))
                return response.content
        except Exception as e:
            logger.error("whatsapp_download_error", media_id=media_id, error=str(e))
            raise
    
    def _get_mimetype(self, filename: str) -> str:
        """Determina el mimetype basado en la extensión del archivo"""
        ext = filename.lower().split(".")[-1]
        mimetypes = {
            "pdf": "application/pdf",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        return mimetypes.get(ext, "application/octet-stream")
