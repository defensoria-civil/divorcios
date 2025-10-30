from fastapi import APIRouter, Depends
from presentation.api.schemas.webhook import WhatsAppInbound
from sqlalchemy.orm import Session
import structlog
from application.use_cases.process_incoming_message import (
    ProcessIncomingMessageUseCase,
    IncomingMessageRequest
)
from infrastructure.persistence.db import SessionLocal
from infrastructure.messaging.waha_service_impl import WAHAWhatsAppService

logger = structlog.get_logger()
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/whatsapp")
async def whatsapp_webhook(payload: WhatsAppInbound, db: Session = Depends(get_db)):
    """Endpoint para webhooks de WhatsApp (WAHA)"""
    logger.info("whatsapp_inbound", payload=payload.model_dump())
    
    if not payload.messages:
        return {"received": True, "status": "no_messages"}
    
    msg = payload.messages[0]
    phone = msg.from_ or msg.chatId or "unknown"
    text = msg.body or ""
    
    # Validar que tengamos un mensaje válido
    if not text.strip():
        return {"received": True, "status": "empty_message"}
    
    # Procesar mensaje con caso de uso
    use_case = ProcessIncomingMessageUseCase(db)
    request = IncomingMessageRequest(phone=phone, text=text)
    
    try:
        response = await use_case.execute(request)
        
        # Enviar respuesta via WhatsApp
        whatsapp = WAHAWhatsAppService()
        await whatsapp.send_message(phone, response.text)
        
        return {
            "received": True,
            "status": "processed",
            "reply": response.text
        }
        
    except Exception as e:
        logger.error("webhook_processing_error", error=str(e), phone=phone)
        
        # Enviar mensaje de error al usuario
        try:
            whatsapp = WAHAWhatsAppService()
            await whatsapp.send_message(
                phone,
                "Disculpá, tuve un problema técnico. Por favor, intentá de nuevo en unos minutos."
            )
        except:
            pass
        
        return {
            "received": True,
            "status": "error",
            "error": str(e)
        }
