from fastapi import APIRouter, Depends
from infrastructure.persistence.db import SessionLocal
from presentation.api.dependencies.security import get_current_operator
from infrastructure.persistence.models import Case

router = APIRouter()

@router.get("/summary")
def metrics_summary(_: dict = Depends(get_current_operator)):
    db = SessionLocal()
    try:
        total_cases = db.query(Case).count()
        return {"total_cases": total_cases}
    finally:
        db.close()
