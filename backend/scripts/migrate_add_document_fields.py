#!/usr/bin/env python3
"""
Script de Migración: Agregar campos para documentos e imágenes al modelo Case.

Campos agregados:
- dni_image_url: referencia al media_id del DNI en WhatsApp
- marriage_cert_url: referencia al media_id del acta de matrimonio
- fecha_matrimonio: fecha de matrimonio extraída del acta
- lugar_matrimonio: lugar de matrimonio extraído del acta

Uso:
    python backend/scripts/migrate_add_document_fields.py
    
O con Docker:
    docker compose exec api python /app/backend/scripts/migrate_add_document_fields.py
"""
import sys
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.persistence.db import engine
from sqlalchemy import text
import structlog

logger = structlog.get_logger()


def add_document_fields():
    """Agrega los nuevos campos al modelo Case"""
    
    migrations = [
        {
            "name": "dni_image_url",
            "sql": "ALTER TABLE cases ADD COLUMN IF NOT EXISTS dni_image_url VARCHAR(255);"
        },
        {
            "name": "marriage_cert_url",
            "sql": "ALTER TABLE cases ADD COLUMN IF NOT EXISTS marriage_cert_url VARCHAR(255);"
        },
        {
            "name": "fecha_matrimonio",
            "sql": "ALTER TABLE cases ADD COLUMN IF NOT EXISTS fecha_matrimonio DATE;"
        },
        {
            "name": "lugar_matrimonio",
            "sql": "ALTER TABLE cases ADD COLUMN IF NOT EXISTS lugar_matrimonio VARCHAR(255);"
        }
    ]
    
    print("\n🔄 Iniciando migración de base de datos...\n")
    
    try:
        with engine.connect() as conn:
            for migration in migrations:
                print(f"📝 Agregando campo: {migration['name']}")
                conn.execute(text(migration['sql']))
                logger.info("field_added", field=migration['name'])
            
            conn.commit()
            print("\n✅ Migración completada exitosamente\n")
            
            print("="*60)
            print("Campos agregados al modelo Case:")
            print("="*60)
            for migration in migrations:
                print(f"  - {migration['name']}")
            print("="*60 + "\n")
            
            return True
            
    except Exception as e:
        logger.error("migration_failed", error=str(e))
        print(f"\n❌ Error en migración: {str(e)}\n")
        return False


if __name__ == "__main__":
    try:
        success = add_document_fields()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Migración cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error("unexpected_error", error=str(e))
        print(f"\n❌ Error inesperado: {str(e)}")
        sys.exit(1)
