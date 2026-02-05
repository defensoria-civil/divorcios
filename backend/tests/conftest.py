"""
Configuración compartida para tests de pytest.

Este archivo proporciona fixtures comunes para todos los tests.
"""
import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from infrastructure.persistence.db import Base


# ==================== Configuración de Base de Datos ====================

def get_test_database_url():
    """
    Obtiene la URL de la base de datos de test.
    
    Prioridad:
    1. Variable de entorno TEST_DATABASE_URL
    2. PostgreSQL local: def_civil_test
    3. SQLite en memoria (fallback)
    """
    test_db_url = os.getenv("TEST_DATABASE_URL")
    
    if test_db_url:
        return test_db_url
    
    # Intentar PostgreSQL local
    postgres_url = "postgresql+psycopg2://postgres:postgres@localhost:5432/def_civil_test"
    
    # Verificar si PostgreSQL está disponible
    try:
        engine = create_engine(postgres_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return postgres_url
    except Exception:
        # Fallback a SQLite en memoria
        print("⚠️  PostgreSQL no disponible, usando SQLite en memoria")
        return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_database_url():
    """URL de la base de datos de test"""
    return get_test_database_url()


@pytest.fixture(scope="session")
def test_engine(test_database_url):
    """
    Engine de SQLAlchemy para tests.
    
    Scope: session - se crea una vez por sesión de tests
    """
    if "sqlite" in test_database_url:
        engine = create_engine(
            test_database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(test_database_url, pool_pre_ping=True)
    
    # Crear extensión pgvector si es PostgreSQL
    if "postgresql" in test_database_url:
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
        except Exception as e:
            print(f"⚠️  No se pudo crear extensión vector: {e}")
    
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Sesión de base de datos para un test.
    
    Scope: function - cada test tiene su propia transacción
    que se hace rollback al finalizar para mantener tests aislados.
    """
    # Crear todas las tablas
    Base.metadata.create_all(bind=test_engine)
    
    # Crear sesión
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=test_engine
    )
    session = TestingSessionLocal()
    
    yield session
    
    # Cleanup: rollback y cierre
    session.rollback()
    session.close()
    
    # Limpiar todas las tablas después del test
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function", autouse=False)
def clean_database(test_engine):
    """
    Limpia completamente la base de datos antes y después de un test.
    
    Uso: Agregar este fixture a tests que necesiten DB limpia
    """
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ==================== Fixtures de Usuario ====================

@pytest.fixture
def test_user_data():
    """Datos de usuario de prueba"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
        "role": "operator",
    }


@pytest.fixture
def admin_user_data():
    """Datos de usuario administrador de prueba"""
    return {
        "username": "adminuser",
        "email": "admin@example.com",
        "password": "adminpass123",
        "full_name": "Admin User",
        "role": "admin",
    }


# ==================== Fixtures de Casos ====================

@pytest.fixture
def sample_case_data():
    """Datos de caso de divorcio de prueba"""
    return {
        "phone": "+5492604123456",
        "type": "unilateral",
        "full_name": "Juan Pérez",
        "dni": "12345678",
        "birth_date": "15/05/1985",
        "domicilio": "San Martín 123, San Rafael, Mendoza",
        "status": "in_progress",
        "current_phase": "personal_data"
    }


# ==================== Fixtures de Configuración ====================

@pytest.fixture(scope="session")
def test_config():
    """Configuración para tests"""
    return {
        "secret_key": "test_secret_key_for_jwt_tokens_min_32_chars",
        "algorithm": "HS256",
        "access_token_expire_minutes": 30,
    }


# ==================== Pytest Configuration ====================

def pytest_configure(config):
    """Configuración de pytest"""
    config.addinivalue_line(
        "markers", "integration: marca tests de integración (lentos)"
    )
    config.addinivalue_line(
        "markers", "unit: marca tests unitarios (rápidos)"
    )
    config.addinivalue_line(
        "markers", "e2e: marca tests end-to-end (muy lentos)"
    )
    config.addinivalue_line(
        "markers", "slow: marca tests lentos"
    )
    config.addinivalue_line(
        "markers", "requires_db: marca tests que requieren base de datos"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: marca tests que requieren API keys externas"
    )
