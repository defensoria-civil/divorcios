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
        """Envía un mensaje de texto. Acepta MSISDN o JID (chatId).
        Reglas:
        - Si viene JID (@c.us/@lid), usarlo tal cual.
        - Si viene solo dígitos y aparenta ser un LID (>=15 dígitos y no empieza con 54/52/55/56/1), enviar como {digits}@lid.
        - En caso contrario, asumir MSISDN y, si es AR sin CC, prefijar 549.
        """
        raw = phone_or_chat.strip()
        # Determinar chatId y phone según formato recibido
        if "@" in raw:
            chat_id = raw  # ya viene como JID (p.ej. 549xxxxxxxxx@c.us o 261...@lid)
            msisdn = raw.split("@")[0]
            is_lid = chat_id.endswith("@lid")
        else:
            msisdn = raw.lstrip("+")
            is_lid = False
            # Heurística: LID-like (WA local id) => muchos dígitos y sin código país habitual
            if len(msisdn) >= 15 and not msisdn.startswith(("54", "52", "55", "56", "1")):
                chat_id = f"{msisdn}@lid"
                is_lid = True
            else:
                # Asumir MSISDN; para Argentina, prefijar 549 si no viene CC
                if not msisdn.startswith("54"):
                    # si viene local (10 dígitos), agregar 549
                    if len(msisdn) == 10:
                        msisdn = f"549{msisdn}"
                    else:
                        msisdn = f"549{msisdn}"
                elif msisdn.startswith("54") and not msisdn.startswith("549"):
                    # agregar 9 móvil si falta
                    msisdn = msisdn.replace("54", "549", 1)
                chat_id = f"{msisdn}@c.us"
        
        url = f"{self.base_url}/api/sendText"
        payload = {
            "session": self.session_name,
            "chatId": chat_id,
            "text": message
        }
        # Para LID no intentamos fallback por phone, ya que WAHA requiere chatId
        
        try:
            async with httpx.AsyncClient(timeout=30, verify=False) as client:
                response = await client.post(url, json=payload, headers=self._headers())
                if response.status_code >= 400:
                    body = response.text
                    logger.warning("whatsapp_send_primary_failed", status=response.status_code, body=body)
                    # Fallback solo si NO es LID; con LID WAHA requiere chatId
                    if not is_lid:
                        alt_payload = {"session": self.session_name, "phone": msisdn, "text": message}
                        alt_resp = await client.post(url, json=alt_payload, headers=self._headers())
                        alt_resp.raise_for_status()
                        result = alt_resp.json()
                        logger.info("whatsapp_message_sent_fallback_phone", phone=msisdn, chat_id=chat_id, result=result)
                        return result
                    else:
                        response.raise_for_status()
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
            is_lid = chat_id.endswith("@lid")
        else:
            msisdn = raw.lstrip("+")
            is_lid = False
            if len(msisdn) >= 15 and not msisdn.startswith(("54", "52", "55", "56", "1")):
                chat_id = f"{msisdn}@lid"
                is_lid = True
            else:
                if not msisdn.startswith("54"):
                    if len(msisdn) == 10:
                        msisdn = f"549{msisdn}"
                    else:
                        msisdn = f"549{msisdn}"
                elif msisdn.startswith("54") and not msisdn.startswith("549"):
                    msisdn = msisdn.replace("54", "549", 1)
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
                    # Fallback: usar 'phone' en lugar de 'chatId' solo si NO es LID
                    if not is_lid:
                        alt_payload = dict(payload)
                        alt_payload.pop("chatId", None)
                        alt_payload["phone"] = msisdn
                        alt_resp = await client.post(url, json=alt_payload, headers=self._headers())
                        alt_resp.raise_for_status()
                        result = alt_resp.json()
                        logger.info("whatsapp_document_sent_fallback_phone", phone=msisdn, chat_id=chat_id, filename=filename, result=result)
                        return result
                    else:
                        response.raise_for_status()
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
