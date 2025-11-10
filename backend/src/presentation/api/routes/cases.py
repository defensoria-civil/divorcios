from fastapi import APIRouter, Depends, Response, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import structlog

from presentation.api.schemas.cases import CaseOut
from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.models import Case, Message
from presentation.api.dependencies.security import get_current_operator
from infrastructure.document.pdf_service_impl import TemplatePDFService

logger = structlog.get_logger()
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_operator)
):
    """
    Lista todos los casos con paginación y filtros
    
    Query params:
    - page: número de página (default: 1)
    - page_size: tamaño de página (default: 50, max: 100)
    - status: filtrar por estado
    - type: filtrar por tipo (unilateral, conjunta)
    - search: buscar por nombre o DNI
    """
    query = db.query(Case)
    
    # Aplicar filtros
    if status:
        query = query.filter(Case.status == status)
    
    if type:
        query = query.filter(Case.type == type)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Case.nombre.ilike(search_term)) | 
            (Case.dni.ilike(search_term))
        )
    
    # Contar total
    total = query.count()
    
    # Paginación
    offset = (page - 1) * page_size
    cases = query.order_by(desc(Case.created_at)).offset(offset).limit(page_size).all()
    
    # Convertir a dict con fechas como strings
    result = []
    for case in cases:
        result.append({
            "id": case.id,
            "phone": case.phone,
            "status": case.status,
            "type": case.type,
            "phase": case.phase,
            "nombre": case.nombre,
            "dni": case.dni,
            "fecha_nacimiento": case.fecha_nacimiento.isoformat() if case.fecha_nacimiento else None,
            "domicilio": case.domicilio,
            "fecha_matrimonio": case.fecha_matrimonio.isoformat() if case.fecha_matrimonio else None,
            "lugar_matrimonio": case.lugar_matrimonio,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
        })
    
    logger.info("cases_listed", count=len(result), total=total, page=page)
    
    return {
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }

@router.get("/stats/summary")
def get_summary_stats(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_operator)
):
    """
    Obtiene estadísticas resumen de todos los casos
    """
    total = db.query(func.count(Case.id)).scalar()
    
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
    
    # Casos nuevos en últimos 7 días
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent = db.query(func.count(Case.id)).filter(
        Case.created_at >= seven_days_ago
    ).scalar()
    
    return {
        "total_cases": total or 0,
        "recent_cases_7d": recent or 0,
        "by_status": {status: count for status, count in by_status},
        "by_type": {type_: count for type_, count in by_type if type_}
    }

@router.get("/{case_id}")
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_operator)
):
    """
    Obtiene detalle completo de un caso incluyendo mensajes
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    # Obtener mensajes del caso
    messages = db.query(Message).filter(
        Message.case_id == case_id
    ).order_by(Message.created_at).all()
    
    result = {
        "id": case.id,
        "phone": case.phone,
        "status": case.status,
        "type": case.type,
        "phase": case.phase,
        "nombre": case.nombre,
        "dni": case.dni,
        "fecha_nacimiento": case.fecha_nacimiento.isoformat() if case.fecha_nacimiento else None,
        "domicilio": case.domicilio,
        "fecha_matrimonio": case.fecha_matrimonio.isoformat() if case.fecha_matrimonio else None,
        "lugar_matrimonio": case.lugar_matrimonio,
        # Perfil económico (declaración jurada)
        "situacion_laboral": case.situacion_laboral,
        "ingreso_mensual_neto": case.ingreso_mensual_neto,
        "vivienda_tipo": case.vivienda_tipo,
        "alquiler_mensual": case.alquiler_mensual,
        "patrimonio_inmuebles": case.patrimonio_inmuebles,
        "patrimonio_registrables": case.patrimonio_registrables,
        "econ_elegible_preliminar": case.econ_elegible_preliminar,
        "econ_razones": case.econ_razones,
        "dni_image_url": case.dni_image_url,
        "marriage_cert_url": case.marriage_cert_url,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }
    
    logger.info("case_retrieved", case_id=case_id, message_count=len(messages))
    return result

@router.patch("/{case_id}")
def update_case(case_id: int, updates: dict, db: Session = Depends(get_db), _: dict = Depends(get_current_operator)):
    """
    Actualiza campos específicos de un caso
    """
    case = db.query(Case).get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    # Lista de campos permitidos para actualización
    allowed_fields = [
        "type", "apellido", "nombres", "dni", "cuit", "domicilio",
        "email", "ocupacion", "nacionalidad", "fecha_nacimiento",
        "apellido_conyuge", "nombres_conyuge", "dni_conyuge", "cuit_conyuge",
        "domicilio_conyuge", "email_conyuge", "ocupacion_conyuge", "nacionalidad_conyuge",
        "fecha_nacimiento_conyuge", "phone_conyuge",
        "fecha_matrimonio", "lugar_matrimonio", "fecha_separacion",
        "acta_numero", "acta_libro", "acta_anio", "acta_foja", "acta_oficina",
        "tiene_hijos", "info_hijos", "tiene_bienes", "info_bienes",
        # Perfil económico
        "situacion_laboral", "ingreso_mensual_neto", "vivienda_tipo", "alquiler_mensual",
        "patrimonio_inmuebles", "patrimonio_registrables", "econ_elegible_preliminar", "econ_razones"
    ]
    
    # Actualizar solo campos permitidos
    updated_fields = []
    for field, value in updates.items():
        if field in allowed_fields and hasattr(case, field):
            # Convertir fechas de string a date si es necesario
            if field in ["fecha_nacimiento", "fecha_matrimonio", "fecha_separacion", "fecha_nacimiento_conyuge"]:
                if value and isinstance(value, str):
                    from datetime import datetime
                    try:
                        value = datetime.fromisoformat(value.replace('Z', '+00:00')).date()
                    except:
                        try:
                            value = datetime.strptime(value, "%Y-%m-%d").date()
                        except:
                            continue
            
            setattr(case, field, value)
            updated_fields.append(field)
    
    if updated_fields:
        case.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(case)
        logger.info("case_updated", case_id=case_id, fields=updated_fields)
    
    return {
        "message": "Caso actualizado exitosamente",
        "updated_fields": updated_fields,
        "case_id": case_id
    }

@router.get("/{case_id}/validate")
def validate_case_data(case_id: int, db: Session = Depends(get_db), _: dict = Depends(get_current_operator)):
    """
    Valida los datos del caso y retorna campos completos y faltantes
    """
    case = db.query(Case).get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    # Definir campos requeridos según tipo de divorcio
    required_fields = {
        "common": [
            {"field": "type", "label": "Tipo de divorcio", "value": case.type},
            {"field": "apellido", "label": "Apellido", "value": case.apellido},
            {"field": "nombres", "label": "Nombres", "value": case.nombres},
            {"field": "dni", "label": "DNI", "value": case.dni},
            {"field": "domicilio", "label": "Domicilio", "value": case.domicilio},
            # Perfil económico (requerido para iniciar BLSG preliminar)
            {"field": "situacion_laboral", "label": "Situación laboral", "value": case.situacion_laboral},
            {"field": "vivienda_tipo", "label": "Tipo de vivienda", "value": case.vivienda_tipo},
            # Cónyuge
            {"field": "apellido_conyuge", "label": "Apellido del cónyuge", "value": case.apellido_conyuge},
            {"field": "nombres_conyuge", "label": "Nombres del cónyuge", "value": case.nombres_conyuge},
            {"field": "dni_conyuge", "label": "DNI del cónyuge", "value": case.dni_conyuge},
            {"field": "fecha_matrimonio", "label": "Fecha de matrimonio", "value": case.fecha_matrimonio},
            {"field": "lugar_matrimonio", "label": "Lugar de matrimonio", "value": case.lugar_matrimonio},
            {"field": "acta_numero", "label": "Número de acta", "value": case.acta_numero},
            {"field": "acta_libro", "label": "Libro de acta", "value": case.acta_libro},
            {"field": "acta_anio", "label": "Año de acta", "value": case.acta_anio},
            {"field": "acta_foja", "label": "Foja de acta", "value": case.acta_foja},
            {"field": "acta_oficina", "label": "Oficina de acta", "value": case.acta_oficina},
        ]
    }
    
    # Separar en completos y faltantes
    complete = []
    missing = []
    
    for field_info in required_fields["common"]:
        field_copy = field_info.copy()
        # Convertir fecha a string si existe
        if field_copy["value"] and hasattr(field_copy["value"], "isoformat"):
            field_copy["value"] = field_copy["value"].isoformat()
        
        if field_copy["value"] is None or field_copy["value"] == "":
            missing.append(field_copy)
        else:
            complete.append(field_copy)
    
    # Información opcional
    optional_info = [
        {"field": "ingreso_mensual_neto", "label": "Ingreso mensual neto", "value": case.ingreso_mensual_neto},
        {"field": "alquiler_mensual", "label": "Alquiler mensual", "value": case.alquiler_mensual},
        {"field": "patrimonio_inmuebles", "label": "Patrimonio: inmuebles", "value": case.patrimonio_inmuebles},
        {"field": "patrimonio_registrables", "label": "Patrimonio: registrables", "value": case.patrimonio_registrables},
        {"field": "tiene_hijos", "label": "¿Tiene hijos?", "value": case.tiene_hijos},
        {"field": "info_hijos", "label": "Información de hijos", "value": case.info_hijos},
        {"field": "tiene_bienes", "label": "¿Tiene bienes?", "value": case.tiene_bienes},
        {"field": "info_bienes", "label": "Información de bienes", "value": case.info_bienes},
    ]
    
    optional_complete = []
    for field_info in optional_info:
        field_copy = field_info.copy()
        if field_copy["value"] is not None:
            optional_complete.append(field_copy)
    
    is_valid = len(missing) == 0
    
    return {
        "case_id": case_id,
        "is_valid": is_valid,
        "complete_fields": complete,
        "missing_fields": missing,
        "optional_fields": optional_complete,
        "completion_percentage": int((len(complete) / len(required_fields["common"])) * 100)
    }

@router.get("/{case_id}/documents/{doc_type}")
async def get_document_image(case_id: int, doc_type: str, db: Session = Depends(get_db), _: dict = Depends(get_current_operator)):
    """
    Descarga la imagen de un documento (DNI o acta de matrimonio)
    doc_type: 'dni' o 'marriage_cert'
    """
    from infrastructure.messaging.waha_service_impl import WAHAWhatsAppService
    
    case = db.query(Case).get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    # Determinar qué documento descargar
    if doc_type == 'dni':
        media_id = case.dni_image_url
        filename = f"dni_caso_{case_id}.jpg"
    elif doc_type == 'marriage_cert':
        media_id = case.marriage_cert_url
        filename = f"acta_matrimonio_caso_{case_id}.jpg"
    else:
        raise HTTPException(status_code=400, detail="Tipo de documento inválido. Usar: dni o marriage_cert")
    
    if not media_id:
        raise HTTPException(status_code=404, detail=f"No se encontró {doc_type} para este caso")
    
    try:
        # Descargar imagen desde WhatsApp
        whatsapp = WAHAWhatsAppService()
        image_bytes = await whatsapp.download_media(media_id)
        
        # Detectar mimetype (generalmente JPG o PNG)
        import imghdr
        image_type = imghdr.what(None, h=image_bytes)
        mimetype = f"image/{image_type}" if image_type else "image/jpeg"
        
        return Response(content=image_bytes, media_type=mimetype)
    except Exception as e:
        logger.error("document_download_error", case_id=case_id, doc_type=doc_type, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error al descargar documento: {str(e)}")

@router.get("/{case_id}/petition.pdf")
def download_petition(case_id: int, db: Session = Depends(get_db), _: dict = Depends(get_current_operator)):
    case = db.query(Case).get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado")
    
    # Construir diccionario completo con TODOS los datos del caso
    case_data = {
        # Tipo de divorcio
        "type": case.type,
        
        # Datos personales del solicitante
        "apellido": case.apellido,
        "nombres": case.nombres,
        "nombre": case.nombre,  # Mantener por compatibilidad
        "dni": case.dni,
        "cuit": case.cuit,
        "fecha_nacimiento": case.fecha_nacimiento,
        "nacionalidad": case.nacionalidad,
        "ocupacion": case.ocupacion,
        "domicilio": case.domicilio,
        "phone": case.phone,
        "email": case.email,
        
        # Datos del cónyuge
        "apellido_conyuge": case.apellido_conyuge,
        "nombres_conyuge": case.nombres_conyuge,
        "nombre_conyuge": case.nombre_conyuge,  # Mantener por compatibilidad
        "dni_conyuge": case.dni_conyuge,
        "cuit_conyuge": case.cuit_conyuge,
        "fecha_nacimiento_conyuge": case.fecha_nacimiento_conyuge,
        "nacionalidad_conyuge": case.nacionalidad_conyuge,
        "ocupacion_conyuge": case.ocupacion_conyuge,
        "domicilio_conyuge": case.domicilio_conyuge,
        "phone_conyuge": case.phone_conyuge,
        "email_conyuge": case.email_conyuge,
        
        # Datos del matrimonio
        "fecha_matrimonio": case.fecha_matrimonio,
        "lugar_matrimonio": case.lugar_matrimonio,
        "fecha_separacion": case.fecha_separacion,
        "ultimo_domicilio_conyugal": case.domicilio,  # Usar domicilio actual si no hay otro
        
        # Datos del acta de matrimonio
        "acta_numero": case.acta_numero,
        "acta_libro": case.acta_libro,
        "acta_anio": case.acta_anio,
        "acta_foja": case.acta_foja,
        "acta_oficina": case.acta_oficina,
        
        # Hijos
        "tiene_hijos": case.tiene_hijos,
        "info_hijos": case.info_hijos,
        
        # Bienes
        "tiene_bienes": case.tiene_bienes,
        "info_bienes": case.info_bienes,
    }
    
    pdf = TemplatePDFService().generate_divorce_petition_pdf(case_data)
    return Response(content=pdf, media_type="application/pdf")
