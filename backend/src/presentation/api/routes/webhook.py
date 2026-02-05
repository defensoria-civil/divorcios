from fastapi import APIRouter, Depends, Request, HTTPException
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
    extracted_media_id = None
    extracted_mime = None
    # Si vino en 'messages' pero sin mediaId, intentar extraer de raw.messages[i].media
    raw_messages = raw.get("messages") if isinstance(raw, dict) else None
    if messages and raw_messages and isinstance(raw_messages, list) and len(raw_messages) > 0:
        try:
            first_raw = raw_messages[0]
            if isinstance(first_raw, dict):
                media = first_raw.get("media") or {}
                url = isinstance(media, dict) and (media.get("url") or media.get("href") or media.get("path"))
                mime = first_raw.get("mimeType") or (isinstance(media, dict) and (media.get("mimetype") or media.get("mime")))
                if url and "/files/" in url:
                    extracted_media_id = url.split("/files/")[-1]
                if mime:
                    extracted_mime = mime
                if not (messages[0].mediaId) and extracted_media_id:
                    messages[0].mediaId = extracted_media_id
                if not (messages[0].mimeType) and extracted_mime:
                    messages[0].mimeType = extracted_mime
        except Exception:
            pass
    if not messages:
        m = raw.get("message") or raw.get("data") or raw.get("payload") or raw.get("msg")
        if m and isinstance(m, dict):
            # Extraer media del payload SIEMPRE, independientemente de si el parseo Pydantic funciona
            media = m.get("media") or {}
            media_id = m.get("mediaId")
            mime_type = m.get("mimeType")
            if not media_id and isinstance(media, dict):
                url = media.get("url") or media.get("href") or media.get("path")
                if url and "/files/" in url:
                    media_id = url.split("/files/")[-1]
                if not mime_type:
                    mime_type = media.get("mimetype") or media.get("mime")
            extracted_media_id = media_id or extracted_media_id
            extracted_mime = mime_type or extracted_mime
            try:
                messages = [WhatsAppMessage(**m)]
            except Exception:
                # Mapear manualmente campos comunes y soportar formato WAHA { media: { url, mimetype } }
                messages = [WhatsAppMessage(
                    id=m.get("id"),
                    from_=m.get("from") or m.get("author") or m.get("sender"),
                    chatId=m.get("chatId") or m.get("from") or m.get("to"),
                    body=m.get("body") or m.get("text") or m.get("caption"),
                    type=m.get("type") or (mime_type.split("/")[0] if isinstance(mime_type, str) else None),
                    mediaId=media_id,
                    mimeType=mime_type,
                    caption=m.get("caption")
                )]
    # Además, si existe raw.payload con media, usarlo como última fuente
    raw_payload = raw.get("payload") if isinstance(raw, dict) else None
    if raw_payload and isinstance(raw_payload, dict):
        try:
            media = raw_payload.get("media") or {}
            url = isinstance(media, dict) and (media.get("url") or media.get("href") or media.get("path"))
            mime = raw_payload.get("mimeType") or (isinstance(media, dict) and (media.get("mimetype") or media.get("mime")))
            if url and "/files/" in url and not extracted_media_id:
                extracted_media_id = url.split("/files/")[-1]
            if mime and not extracted_mime:
                extracted_mime = mime
        except Exception:
            pass
    
    if not messages:
        # Payload sin mensajes: consideramos la request inválida.
        raise HTTPException(status_code=400, detail="No messages in payload")
    
    msg = messages[0]
    phone_raw = msg.from_ or msg.chatId or "unknown"
    # Normalizar el número de teléfono (remover @lid, @c.us, etc.)
    phone = normalize_whatsapp_phone(phone_raw)
    text = msg.body or msg.caption or ""  # Usar caption si es imagen
    
    # NUEVO: Detectar si hay media adjunto (imagen)
    media_id = extracted_media_id or None
    mime_type = extracted_mime or None
    if msg.mediaId and not media_id:
        media_id = msg.mediaId
    if msg.mimeType and not mime_type:
        mime_type = msg.mimeType
    if media_id:
        logger.info("media_received", phone=phone, media_id=media_id, type=msg.type, mime=mime_type)
    
    # Validar que tengamos contenido (texto o imagen/documento)
    if not text.strip() and not media_id:
        return {"received": True, "status": "empty_message"}
    
    # Procesar mensaje con caso de uso
    use_case = ProcessIncomingMessageUseCase(db)
    request = IncomingMessageRequest(
        phone=phone, 
        text=text,
        media_id=media_id,
        mime_type=mime_type
    )
    
    try:
        response = await use_case.execute(request)

        # Determinar si corresponde enviar respuesta al usuario
        should_send = getattr(response, "should_send", True)
        text_out = getattr(response, "text", None)

        if should_send and text_out:
            # Enviar respuesta via WhatsApp (usar el ID original con @lid)
            whatsapp = WAHAWhatsAppService()
            await whatsapp.send_message(phone_raw, text_out)

        return {
            "received": True,
            "status": "processed",
            "reply": text_out,
            "sent": bool(should_send and text_out),
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
