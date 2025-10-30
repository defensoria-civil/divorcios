from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

class CaseOut(BaseModel):
    id: int
    phone: str
    status: str
    type: Optional[str]
    phase: str
    nombre: Optional[str]
    dni: Optional[str]
    fecha_nacimiento: Optional[date]
    domicilio: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
