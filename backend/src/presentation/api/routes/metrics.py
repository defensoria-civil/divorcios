from fastapi import APIRouter, Depends
from sqlalchemy import func, Date, cast
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import structlog

from infrastructure.persistence.db import get_db
from presentation.api.dependencies.security import get_current_operator
from infrastructure.persistence.models import Case

logger = structlog.get_logger()
router = APIRouter()

@router.get("/summary")
def metrics_summary(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_operator)
):
    """
    Resumen general de métricas del sistema
    """
    total = db.query(func.count(Case.id)).scalar() or 0
    
    # Casos nuevos en últimos 7 días
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_7d = db.query(func.count(Case.id)).filter(
        Case.created_at >= seven_days_ago
    ).scalar() or 0
    
    # Casos nuevos en últimos 30 días
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_30d = db.query(func.count(Case.id)).filter(
        Case.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Casos por estado
    by_status = db.query(
        Case.status,
        func.count(Case.id)
    ).group_by(Case.status).all()
    
    # Casos por tipo
    by_type = db.query(
        Case.type,
        func.count(Case.id)
    ).filter(Case.type.isnot(None)).group_by(Case.type).all()
    
    return {
        "total_cases": total,
        "recent_cases_7d": recent_7d,
        "recent_cases_30d": recent_30d,
        "cases_by_status": {status: count for status, count in by_status},
        "cases_by_type": {type_: count for type_, count in by_type if type_}
    }

@router.get("/by_status")
def metrics_by_status(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_operator)
):
    """
    Distribución de casos por estado
    """
    results = db.query(
        Case.status,
        func.count(Case.id).label('count')
    ).group_by(Case.status).all()
    
    total = sum(count for _, count in results)
    
    return [
        {
            "status": status,
            "count": count,
            "percent": count / total if total > 0 else 0
        }
        for status, count in results
    ]

@router.get("/by_type")
def metrics_by_type(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_operator)
):
    """
    Distribución de casos por tipo (unilateral vs conjunta)
    """
    results = db.query(
        Case.type,
        func.count(Case.id).label('count')
    ).filter(Case.type.isnot(None)).group_by(Case.type).all()
    
    return [
        {"type": type_, "count": count}
        for type_, count in results
    ]

@router.get("/timeline")
def metrics_timeline(
    days: int = 30,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_operator)
):
    """
    Casos creados por día en los últimos N días
    
    Query params:
    - days: número de días hacia atrás (default: 30)
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    results = db.query(
        cast(Case.created_at, Date).label('date'),
        func.count(Case.id).label('count')
    ).filter(
        Case.created_at >= since
    ).group_by(
        cast(Case.created_at, Date)
    ).order_by('date').all()
    
    return [
        {
            "date": date.isoformat(),
            "count": count
        }
        for date, count in results
    ]
