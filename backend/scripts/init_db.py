#!/usr/bin/env python3
"""
Script de Inicialización de Base de Datos.

Responsabilidades:
- Crear extensión pgvector
- Crear todas las tablas del sistema
- Crear usuario admin inicial
- Es idempotente (puede ejecutarse múltiples veces)

Uso:
    python backend/scripts/init_db.py
    
O con Docker:
    docker compose exec api python /app/backend/scripts/init_db.py
"""
import sys
from pathlib import Path

# Agregar src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.persistence.db import engine, Base
from infrastructure.persistence.models import (
    Case, 
    Message, 
    Memory, 
    SemanticKnowledge,
    User
)
from infrastructure.persistence.repositories import UserRepository
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import structlog

logger = structlog.get_logger()


def create_pgvector_extension():
    """Crea la extensión pgvector si no existe"""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
        logger.info("pgvector_extension_created")
        return True
    except Exception as e:
        logger.error("pgvector_extension_failed", error=str(e))
        return False


def create_tables():
    """Crea todas las tablas del sistema"""
    try:
        Base.metadata.create_all(bind=engine)
        tables = list(Base.metadata.tables.keys())
        logger.info("database_tables_created", tables=tables, count=len(tables))
        return True
    except Exception as e:
        logger.error("database_tables_creation_failed", error=str(e))
        return False


def create_admin_user():
    """Crea el usuario admin inicial si no existe"""
    session = Session(engine)
    user_repo = UserRepository(session)
    
    try:
        # Verificar si ya existe un admin
        existing_admin = user_repo.get_by_username("admin")
        
        if existing_admin:
            logger.info("admin_user_already_exists", username=existing_admin.username)
            return True
        
        # Crear usuario admin
        admin = user_repo.create_user(
            username="admin",
            email="admin@defensoria-sr.gob.ar",
            password="changeme123",  # ⚠️ CAMBIAR EN PRODUCCIÓN
            full_name="Administrador",
            role="admin"
        )
        
        logger.info(
            "admin_user_created", 
            username=admin.username,
            email=admin.email
        )
        
        print("\n" + "="*60)
        print("✅ Usuario admin creado exitosamente")
        print("="*60)
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Password: changeme123")
        print("="*60)
        print("⚠️  IMPORTANTE: Cambiar la contraseña en producción")
        print("="*60 + "\n")
        
        session.commit()
        return True
        
    except IntegrityError as e:
        logger.warning("admin_user_creation_skipped", reason="Already exists")
        session.rollback()
        return True
        
    except Exception as e:
        logger.error("admin_user_creation_failed", error=str(e))
        session.rollback()
        return False
        
    finally:
        session.close()


def init_database():
    """
    Inicializa la base de datos completa.
    
    Pasos:
    1. Crear extensión pgvector
    2. Crear todas las tablas
    3. Crear usuario admin
    
    Returns:
        bool: True si la inicialización fue exitosa
    """
    print("\n🚀 Iniciando configuración de base de datos...\n")
    
    # Paso 1: pgvector
    print("📦 Creando extensión pgvector...")
    if not create_pgvector_extension():
        print("❌ Error creando extensión pgvector")
        return False
    print("✅ Extensión pgvector lista\n")
    
    # Paso 2: Tablas
    print("🗃️  Creando tablas del sistema...")
    if not create_tables():
        print("❌ Error creando tablas")
        return False
    print("✅ Tablas creadas exitosamente\n")
    
    # Paso 3: Usuario admin
    print("👤 Creando usuario administrador...")
    if not create_admin_user():
        print("❌ Error creando usuario admin")
        return False
    
    print("\n" + "="*60)
    print("✅ Base de datos inicializada correctamente")
    print("="*60)
    print("\nTablas disponibles:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
    print("\n" + "="*60 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = init_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Inicialización cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        print(f"\n❌ Error inesperado: {str(e)}")
        sys.exit(1)
