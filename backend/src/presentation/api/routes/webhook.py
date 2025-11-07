from fastapi import APIRouter, Depends, Request
from presentation.api.schemas.webhook import WhatsAppInbound, WhatsAppMessage
from sqlalchemy.orm import Session
import structlog
from application.use_cases.process_incoming_message import (
    ProcessIncomingMessageUseCase,
    IncomingMessageRequest
)
from infrastructure.persistence.db import SessionLocal
from infrastructure.messaging.waha_service_impl import WAHAWhatsAppService
from infrastructure.utils.phone_utils import normalize_whatsapp_phone

logger = structlog.get_logger()
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/whatsapp")
async def whatsapp_webhook(payload: WhatsAppInbound, request: Request, db: Session = Depends(get_db)):
    """Endpoint para webhooks de WhatsApp (WAHA)"""
    raw = await request.json()
    logger.info("whatsapp_inbound", payload=payload.model_dump(), raw=raw)
    
    # Manejar formatos alternativos de WAHA (v2025): { message: {...} } o { data: {...} } o { payload: {...} }
    messages = list(payload.messages or [])
    if not messages:
        m = raw.get("message") or raw.get("data") or raw.get("payload") or raw.get("msg")
        if m and isinstance(m, dict):
            try:
                messages = [WhatsAppMessage(**m)]
            except Exception:
                # Mapear manualmente campos comunes
                messages = [WhatsAppMessage(
                    id=m.get("id"),
                    from_=m.get("from") or m.get("author") or m.get("sender"),
                    chatId=m.get("chatId") or m.get("from") or m.get("to"),
                    body=m.get("body") or m.get("text") or m.get("caption"),
                    type=m.get("type"),
                    mediaId=m.get("mediaId"),
                    mimeType=m.get("mimeType"),
                    caption=m.get("caption")
                )]
    
    if not messages:
        return {"received": True, "status": "no_messages"}
    
    msg = messages[0]
    phone_raw = msg.from_ or msg.chatId or "unknown"
    # Normalizar el número de teléfono (remover @lid, @c.us, etc.)
    phone = normalize_whatsapp_phone(phone_raw)
    text = msg.body or msg.caption or ""  # Usar caption si es imagen
    
    # NUEVO: Detectar si hay media adjunto (imagen)
    media_id = None
    if msg.type == 'image' and msg.mediaId:
        media_id = msg.mediaId
        logger.info("image_received", phone=phone, media_id=media_id)
    
    # Validar que tengamos contenido (texto o imagen)
    if not text.strip() and not media_id:
        return {"received": True, "status": "empty_message"}
    
    # Procesar mensaje con caso de uso
    use_case = ProcessIncomingMessageUseCase(db)
    request = IncomingMessageRequest(
        phone=phone, 
        text=text,
        media_id=media_id  # Pasar media_id al use case
    )
    
    try:
        response = await use_case.execute(request)
        
        # Enviar respuesta via WhatsApp (usar el ID original con @lid)
        whatsapp = WAHAWhatsAppService()
        await whatsapp.send_message(phone_raw, response.text)
        
        return {
            "received": True,
            "status": "processed",
            "reply": response.text
        }
        
    except Exception as e:
        logger.error("webhook_processing_error", error=str(e), phone=phone)
        
        # Enviar mensaje de error al usuario (usar el ID original con @lid)
        try:
            whatsapp = WAHAWhatsAppService()
            await whatsapp.send_message(
                phone_raw,
                "Disculpá, tuve un problema técnico. Por favor, intentá de nuevo en unos minutos."
            )
        except:
            pass
        
        return {
            "received": True,
            "status": "error",
            "error": str(e)
        }
