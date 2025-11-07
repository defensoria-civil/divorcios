from pydantic import BaseModel, Field
from typing import Optional, List

class WhatsAppMessage(BaseModel):
    id: Optional[str] = None
    from_: Optional[str] = Field(default=None, alias="from")
    chatId: Optional[str] = None
    body: Optional[str] = None
    type: Optional[str] = None  # 'text', 'image', 'video', 'document', etc.
    timestamp: Optional[int] = None
    
    # Campos de media
    mediaId: Optional[str] = None  # ID del archivo multimedia
    mediaUrl: Optional[str] = None  # URL del archivo (si está disponible)
    mimeType: Optional[str] = None  # Tipo MIME del archivo
    caption: Optional[str] = None  # Caption/leyenda de la imagen

class WhatsAppInbound(BaseModel):
    instanceId: Optional[str] = None
    messages: List[WhatsAppMessage] = []
