import os
os.environ['PGCLIENTENCODING'] = 'UTF8'

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

def get_db():
    """Dependency para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Ensure vector extension and create tables
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        except Exception:
            # Si falla (por permisos), continuar; el tipo vector debe existir en la imagen de Postgres pgvector
            pass
    # Import models to register metadata
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Lightweight idempotent migrations
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE cases ADD COLUMN IF NOT EXISTS dni_back_url VARCHAR(255)"))
            conn.commit()
    except Exception:
        # Ignore migration errors in init; assume managed elsewhere
        pass
