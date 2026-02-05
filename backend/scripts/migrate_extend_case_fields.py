#!/usr/bin/env python3
"""
Migración: ampliar campos del modelo Case según análisis de escritos oficiales.

Agrega columnas si no existen (idempotente):
- Datos de contacto y perfil: email, ocupacion, nacionalidad
- Fechas clave: fecha_separacion
- Acta de matrimonio: acta_numero, acta_libro, acta_anio, acta_foja, acta_oficina
- Cónyuge: apellido_conyuge, nombres_conyuge, dni_conyuge, domicilio_conyuge,
           fecha_nacimiento_conyuge, ocupacion_conyuge, nacionalidad_conyuge,
           phone_conyuge, email_conyuge

Uso:
    python backend/scripts/migrate_extend_case_fields.py
"""
import os
import sys
from pathlib import Path

# Fix encoding issue with psycopg2 on Windows when DB contains non-UTF8 data
os.environ['PGCLIENTENCODING'] = 'LATIN1'

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.persistence.db import engine
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

MIGRATIONS = [
    ("email", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS email VARCHAR(120);"),
    ("ocupacion", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS ocupacion VARCHAR(80);"),
    ("nacionalidad", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS nacionalidad VARCHAR(32) DEFAULT 'argentino/a';"),
    ("fecha_separacion", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS fecha_separacion DATE;"),
    # Acta
    ("acta_numero", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS acta_numero VARCHAR(16);"),
    ("acta_libro", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS acta_libro VARCHAR(32);"),
    ("acta_anio", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS acta_anio VARCHAR(8);"),
    ("acta_foja", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS acta_foja VARCHAR(16);"),
    ("acta_oficina", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS acta_oficina VARCHAR(120);"),
    # Cónyuge
    ("apellido_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS apellido_conyuge VARCHAR(80);"),
    ("nombres_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS nombres_conyuge VARCHAR(80);"),
    ("dni_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS dni_conyuge VARCHAR(16);"),
    ("domicilio_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS domicilio_conyuge TEXT;"),
    ("fecha_nacimiento_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS fecha_nacimiento_conyuge DATE;"),
    ("ocupacion_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS ocupacion_conyuge VARCHAR(80);"),
    ("nacionalidad_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS nacionalidad_conyuge VARCHAR(32) DEFAULT 'argentino/a';"),
    ("phone_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS phone_conyuge VARCHAR(32);"),
    ("email_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS email_conyuge VARCHAR(120);"),
]

def run():
    print("\n🔄 Iniciando migración de campos extendidos...\n")
    try:
        with engine.connect() as conn:
            for name, sql in MIGRATIONS:
                print(f"📝 Agregando campo: {name}")
                conn.execute(text(sql))
                logger.info("field_added", field=name)
            conn.commit()
        print("\n✅ Migración completada\n")
        return True
    except Exception as e:
        logger.error("migration_failed", error=str(e))
        print(f"\n❌ Error en migración: {e}\n")
        return False

if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
