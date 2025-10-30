from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session
from typing import List
from presentation.api.schemas.cases import CaseOut
from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.models import Case
from presentation.api.dependencies.security import get_current_operator
from infrastructure.document.pdf_service_impl import SimplePDFService

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[CaseOut])
def list_cases(db: Session = Depends(get_db), _: dict = Depends(get_current_operator)):
    return db.query(Case).order_by(Case.created_at.desc()).limit(100).all()

@router.get("/{case_id}/petition.pdf")
def download_petition(case_id: int, db: Session = Depends(get_db), _: dict = Depends(get_current_operator)):
    case = db.query(Case).get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    pdf = SimplePDFService().generate_divorce_petition_pdf({
        "type": case.type,
        "nombre": case.nombre,
        "dni": case.dni,
        "domicilio": case.domicilio,
    })
    return Response(content=pdf, media_type="application/pdf")
