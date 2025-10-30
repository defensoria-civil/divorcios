from pydantic import BaseModel, Field
from typing import Optional, List

class WhatsAppMessage(BaseModel):
    id: Optional[str] = None
    from_: Optional[str] = Field(default=None, alias="from")
    chatId: Optional[str] = None
    body: Optional[str] = None
    type: Optional[str] = None
    timestamp: Optional[int] = None

class WhatsAppInbound(BaseModel):
    instanceId: Optional[str] = None
    messages: List[WhatsAppMessage] = []
