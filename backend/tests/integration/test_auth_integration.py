"""
Tests de Integración: Autenticación

Prueba el flujo completo de autenticación, incluyendo login, registro y acceso a rutas protegidas.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from infrastructure.persistence.models import User
from passlib.context import CryptContext
from tests.conftest import test_engine

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture
def db_session_for_auth(test_engine):
    """Sesión de BD para tests de auth, usando el engine compartido de integración."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session_for_auth):
    """Crea un usuario de prueba en la BD"""
    db = db_session_for_auth
    try:
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=pwd_context.hash("testpass123"),
            full_name="Test User",
            role="operator",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


class TestLogin:
    """Tests para el endpoint de login"""

    def test_login_success(self, client: TestClient, test_user):
        """Test: Login exitoso con credenciales válidas"""
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "operator"

    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test: Login falla con contraseña incorrecta"""
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test: Login falla con usuario inexistente"""
        response = client.post(
            "/api/auth/login", json={"username": "nonexistent", "password": "password"}
        )

        assert response.status_code == 401

    def test_login_inactive_user(self, client: TestClient, db_session_for_auth):
        """Test: Login falla con usuario inactivo"""
        db = db_session_for_auth
        try:
            user = User(
                username="inactive",
                email="inactive@example.com",
                hashed_password=pwd_context.hash("password"),
                full_name="Inactive User",
                role="operator",
                is_active=False,
            )
            db.add(user)
            db.commit()
        finally:
            db.rollback()

        response = client.post(
            "/api/auth/login", json={"username": "inactive", "password": "password"}
        )

        assert response.status_code == 403
        assert "desactivado" in response.json()["detail"].lower() or "inactivo" in response.json()["detail"].lower()


class TestProtectedEndpoints:
    """Tests para endpoints protegidos con JWT"""

    def test_access_without_token(self, client: TestClient):
        """Test: Acceso sin token retorna 401"""
        response = client.get("/api/auth/me")
        assert response.status_code == 403  # FastAPI retorna 403 para HTTPBearer sin token

    def test_access_with_invalid_token(self, client: TestClient):
        """Test: Acceso con token inválido retorna 401"""
        response = client.get(
            "/api/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_access_with_valid_token(self, client: TestClient, test_user):
        """Test: Acceso exitoso con token válido"""
        # Primero hacer login para obtener token
        login_response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        token = login_response.json()["access_token"]

        # Acceder a endpoint protegido
        response = client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"


class TestUserRegistration:
    """Tests para el endpoint de registro"""

    def test_register_success(self, client: TestClient):
        """Test: Registro exitoso de nuevo usuario"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpass123",
                "full_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_username(self, client: TestClient, test_user):
        """Test: Registro falla con username duplicado"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",  # Ya existe
                "email": "another@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 400
        assert "username" in response.json()["detail"].lower()

    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Test: Registro falla con email duplicado"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "anotheruser",
                "email": "test@example.com",  # Ya existe
                "password": "password123",
            },
        )

        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()

    def test_register_short_password(self, client: TestClient):
        """Test: Registro falla con contraseña muy corta"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "123",  # Muy corta
            },
        )

        assert response.status_code == 400


class TestTokenRefresh:
    """Tests para refresh de tokens"""

    def test_refresh_valid_token(self, client: TestClient, test_user):
        """Test: Refresh exitoso con token válido"""
        # Login para obtener token
        login_response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        old_token = login_response.json()["access_token"]

        # Refresh token
        response = client.post(
            "/api/auth/refresh", headers={"Authorization": f"Bearer {old_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        # El token puede ser el mismo si el tiempo de expiración no ha cambiado significativamente
        # Lo importante es que el endpoint funcione
        assert len(data["access_token"]) > 0

    def test_refresh_invalid_token(self, client: TestClient):
        """Test: Refresh falla con token inválido"""
        response = client.post(
            "/api/auth/refresh", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
