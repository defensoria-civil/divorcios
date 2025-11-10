#!/usr/bin/env python3
"""
Migración: agregar columnas para Perfil Económico (BLSG) al modelo Case.

Campos:
- situacion_laboral VARCHAR(32)
- ingreso_mensual_neto INTEGER
- vivienda_tipo VARCHAR(16)
- alquiler_mensual INTEGER
- patrimonio_inmuebles TEXT
- patrimonio_registrables TEXT
- econ_elegible_preliminar BOOLEAN
- econ_razones TEXT

Uso:
    python backend/scripts/migrate_add_economic_profile.py
"""
import sys
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.persistence.db import engine
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

MIGRATIONS = [
    ("situacion_laboral", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS situacion_laboral VARCHAR(32);"),
    ("ingreso_mensual_neto", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS ingreso_mensual_neto INTEGER;"),
    ("vivienda_tipo", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS vivienda_tipo VARCHAR(16);"),
    ("alquiler_mensual", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS alquiler_mensual INTEGER;"),
    ("patrimonio_inmuebles", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS patrimonio_inmuebles TEXT;"),
    ("patrimonio_registrables", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS patrimonio_registrables TEXT;"),
    ("econ_elegible_preliminar", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS econ_elegible_preliminar BOOLEAN;"),
    ("econ_razones", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS econ_razones TEXT;"),
    # Spouse
    ("situacion_laboral_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS situacion_laboral_conyuge VARCHAR(32);"),
    ("ingreso_mensual_neto_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS ingreso_mensual_neto_conyuge INTEGER;"),
    ("vivienda_tipo_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS vivienda_tipo_conyuge VARCHAR(16);"),
    ("alquiler_mensual_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS alquiler_mensual_conyuge INTEGER;"),
    ("patrimonio_inmuebles_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS patrimonio_inmuebles_conyuge TEXT;"),
    ("patrimonio_registrables_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS patrimonio_registrables_conyuge TEXT;"),
    ("econ_elegible_preliminar_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS econ_elegible_preliminar_conyuge BOOLEAN;"),
    ("econ_razones_conyuge", "ALTER TABLE cases ADD COLUMN IF NOT EXISTS econ_razones_conyuge TEXT;")
]

def run():
    print("\n🔄 Iniciando migración de Perfil Económico (BLSG)...\n")
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
    sys.exit(0 if run() else 1)
