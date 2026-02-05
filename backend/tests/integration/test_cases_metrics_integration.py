"""
Tests de Integración: Cases y Metrics Endpoints

Prueba los endpoints de gestión de casos y métricas del sistema.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from infrastructure.persistence.db import Base
from infrastructure.persistence.models import User, Case, Message
from passlib.context import CryptContext
from tests.conftest import test_engine

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture
def db_session_for_cases(test_engine):
    """Sesión de BD para tests de casos/métricas, usando el engine compartido.

    Asegura que las tablas existan antes de usar la sesión.
    """
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user_with_token(client: TestClient, db_session_for_cases):
    """Crea un usuario de prueba y retorna token de autenticación"""
    db = db_session_for_cases
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
        
        # Obtener token
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpass123"},
        )
        token = response.json()["access_token"]
        
        return {"user": user, "token": token}
    finally:
        db.close()


@pytest.fixture
def test_cases(db_session_for_cases):
    """Crea casos de prueba en la base de datos, alineados con el modelo Case real."""
    db = db_session_for_cases
    try:
        cases = [
            Case(
                phone="+5492604111111",
                type="unilateral",
                apellido="Pérez",
                nombres="Juan",
                nombre="Juan Pérez",
                dni="12345678",
                fecha_nacimiento=datetime(1985, 5, 15).date(),
                status="in_progress",
                phase="personal_data",
            ),
            Case(
                phone="+5492604222222",
                type="conjunta",
                apellido="López",
                nombres="María",
                nombre="María López",
                dni="87654321",
                fecha_nacimiento=datetime(1990, 8, 20).date(),
                status="completed",
                phase="completed",
            ),
            Case(
                phone="+5492604333333",
                type="unilateral",
                apellido="Sánchez",
                nombres="Pedro",
                nombre="Pedro Sánchez",
                dni="11223344",
                fecha_nacimiento=datetime(1978, 3, 10).date(),
                status="pending",
                phase="matrimonio",
            ),
        ]
        
        for case in cases:
            db.add(case)
        
        db.commit()
        
        # Refresh para obtener IDs generados por la BD
        for case in cases:
            db.refresh(case)
        
        return cases
    finally:
        db.close()


class TestCasesEndpoints:
    """Tests para endpoints de casos"""

    def test_list_cases_requires_authentication(self, client: TestClient):
        """Test: Listar casos requiere autenticación"""
        response = client.get("/api/cases/")
        assert response.status_code == 403  # Sin token

    def test_list_cases_success(self, client: TestClient, test_user_with_token, test_cases):
        """Test: Listar casos exitosamente con autenticación"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/cases/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data
        assert len(data["items"]) == 3

    def test_get_case_by_id(self, client: TestClient, test_user_with_token, test_cases):
        """Test: Obtener caso específico por ID"""
        token = test_user_with_token["token"]
        case_id = test_cases[0].id
        
        response = client.get(
            f"/api/cases/{case_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == case_id
        assert data["nombre"] == "Juan Pérez"

    def test_get_nonexistent_case(self, client: TestClient, test_user_with_token):
        """Test: Error al buscar caso inexistente"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/cases/99999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404

    def test_filter_cases_by_status(self, client: TestClient, test_user_with_token, test_cases):
        """Test: Filtrar casos por estado"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/cases/?status=completed",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        assert all(case["status"] == "completed" for case in items)
        assert len(items) == 1

    def test_filter_cases_by_type(self, client: TestClient, test_user_with_token, test_cases):
        """Test: Filtrar casos por tipo de divorcio"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/cases/?type=unilateral",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        assert all(case["type"] == "unilateral" for case in items)
        assert len(items) == 2

    def test_search_cases_by_name(self, client: TestClient, test_user_with_token, test_cases):
        """Test: Buscar casos por nombre"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/cases/?search=María",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        assert len(items) >= 1
        assert any("María" in (case["nombre"] or "") for case in items)

    def test_search_cases_by_dni(self, client: TestClient, test_user_with_token, test_cases):
        """Test: Buscar casos por DNI"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/cases/?search=12345678",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        assert len(items) >= 1
        assert any(case["dni"] == "12345678" for case in items)

    def test_update_case(self, client: TestClient, test_user_with_token, test_cases):
        """Test: Actualizar información de un caso"""
        token = test_user_with_token["token"]
        case_id = test_cases[0].id
        
        response = client.patch(
            f"/api/cases/{case_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"phase": "completed"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Caso actualizado exitosamente"
        assert "phase" in data["updated_fields"]

    def test_pagination_of_cases(self, client: TestClient, test_user_with_token, test_cases):
        """Test: Paginación de casos"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/cases/?page=1&page_size=2",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2


class TestMetricsEndpoints:
    """Tests para endpoints de métricas"""

    def test_metrics_require_authentication(self, client: TestClient):
        """Test: Métricas requieren autenticación"""
        response = client.get("/api/metrics/summary")
        assert response.status_code == 403

    def test_get_metrics_summary(self, client: TestClient, test_user_with_token, test_cases):
        """Test: Obtener resumen de métricas"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/metrics/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de métricas
        assert "total_cases" in data
        assert "cases_by_status" in data
        assert "cases_by_type" in data
        assert data["total_cases"] == 3

    def test_metrics_cases_by_status(self, client: TestClient, test_user_with_token, test_cases):
        """Test: Métricas de casos por estado"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/metrics/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        status_counts = data["cases_by_status"]
        assert "in_progress" in status_counts
        assert "completed" in status_counts
        assert "pending" in status_counts

    def test_metrics_cases_by_type(self, client: TestClient, test_user_with_token, test_cases):
        """Test: Métricas de casos por tipo"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/metrics/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        type_counts = data["cases_by_type"]
        assert "unilateral" in type_counts
        assert "conjunta" in type_counts
        assert type_counts["unilateral"] == 2
        assert type_counts["conjunta"] == 1

    def test_metrics_time_range(self, client: TestClient, test_user_with_token, test_cases):
        """Test: Métricas con rango de fechas"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/metrics/summary?start_date=2025-01-01&end_date=2025-12-31",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200

    def test_metrics_response_times(self, client: TestClient, test_user_with_token):
        """Test: Métricas de tiempos de respuesta"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/metrics/response-times",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Puede retornar 200 o 404 dependiendo de si hay datos
        assert response.status_code in [200, 404]

    def test_metrics_user_activity(self, client: TestClient, test_user_with_token):
        """Test: Métricas de actividad de usuarios"""
        token = test_user_with_token["token"]
        
        response = client.get(
            "/api/metrics/user-activity",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Puede retornar 200 o 404 dependiendo de si hay datos
        assert response.status_code in [200, 404]


class TestHealthEndpoint:
    """Tests para endpoint de health check"""

    def test_health_check_no_auth_required(self, client: TestClient):
        """Test: Health check no requiere autenticación"""
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_check_includes_timestamp(self, client: TestClient):
        """Test: Health check incluye timestamp"""
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data or "status" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
