#!/usr/bin/env python3
"""
Script para migrar números de teléfono existentes en la base de datos.
Remueve el sufijo @lid o @c.us de los números existentes.

Uso:
    python scripts/migrate_phone_numbers.py
"""

import sys
import os

# Añadir el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from infrastructure.persistence.models import Case
from infrastructure.utils.phone_utils import normalize_whatsapp_phone
from core.config import settings
import structlog

logger = structlog.get_logger()


def migrate_phone_numbers(dry_run=True):
    """
    Migra los números de teléfono en la base de datos.
    
    Args:
        dry_run: Si es True, solo muestra qué cambios se harían sin aplicarlos
    """
    # Crear conexión a la base de datos
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Obtener todos los casos
        cases = db.query(Case).all()
        
        logger.info("migration_start", total_cases=len(cases), dry_run=dry_run)
        
        updated_count = 0
        skipped_count = 0
        
        for case in cases:
            old_phone = case.phone
            new_phone = normalize_whatsapp_phone(old_phone)
            
            # Si el número cambió, actualizarlo
            if old_phone != new_phone:
                logger.info(
                    "phone_migration",
                    case_id=case.id,
                    old_phone=old_phone,
                    new_phone=new_phone,
                    dry_run=dry_run
                )
                
                if not dry_run:
                    case.phone = new_phone
                    updated_count += 1
                else:
                    updated_count += 1
            else:
                skipped_count += 1
        
        if not dry_run:
            db.commit()
            logger.info("migration_committed", updated=updated_count, skipped=skipped_count)
        else:
            logger.info("migration_dry_run", would_update=updated_count, skipped=skipped_count)
            print(f"\n✅ Dry run completado:")
            print(f"   - Se actualizarían {updated_count} registros")
            print(f"   - Se saltarían {skipped_count} registros (ya normalizados)")
            print(f"\nEjecuta con --apply para aplicar los cambios")
        
    except Exception as e:
        db.rollback()
        logger.error("migration_error", error=str(e))
        raise
    finally:
        db.close()


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrar números de teléfono en la base de datos')
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Aplicar los cambios (por defecto solo muestra lo que haría)'
    )
    
    args = parser.parse_args()
    
    if args.apply:
        print("⚠️  APLICANDO CAMBIOS A LA BASE DE DATOS...")
        response = input("¿Estás seguro? (escribe 'SI' para confirmar): ")
        if response != 'SI':
            print("❌ Migración cancelada")
            return
    else:
        print("🔍 Ejecutando en modo DRY RUN (sin cambios reales)...")
    
    migrate_phone_numbers(dry_run=not args.apply)
    
    if args.apply:
        print("\n✅ Migración completada exitosamente!")
    

if __name__ == "__main__":
    main()
