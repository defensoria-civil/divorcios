"""Fixtures compartidos para tests de integración de la API.

- Usa el engine de tests definido en tests/conftest.py
- Define un override único de get_db para toda la sesión de tests de integración
- Expone un TestClient común para todos los módulos de tests de integración
"""
import pytest
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from presentation.api.main import app
from infrastructure.persistence.db import Base, get_db
from tests.conftest import test_engine


@pytest.fixture(scope="session")
def client(test_engine):
    """Cliente de pruebas compartido con override de DB único."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    return TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_db_tables(test_engine):
    """Crear y dropear tablas alrededor de cada test de integración.

    Nota: esto se ejecuta automáticamente para cualquier test en tests/integration.
    """
    Base.metadata.create_all(bind=test_engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=test_engine)
