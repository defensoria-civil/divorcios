import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.persistence.db import Base
from application.use_cases.process_incoming_message import (
    ProcessIncomingMessageUseCase,
    IncomingMessageRequest
)

# Configuración de DB de prueba
TEST_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/def_civil_test"

@pytest.fixture(scope="function")
def test_db():
    """Crea DB de test limpia para cada test"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_complete_divorce_flow_unilateral(test_db):
    """Test del flujo completo de divorcio unilateral"""
    use_case = ProcessIncomingMessageUseCase(test_db)
    phone = "+5492604123456"
    
    # 1. Inicio
    request = IncomingMessageRequest(phone=phone, text="Hola")
    response = await use_case.execute(request)
    assert "tipo de divorcio" in response.text.lower()
    
    # 2. Tipo de divorcio
    request = IncomingMessageRequest(phone=phone, text="unilateral")
    response = await use_case.execute(request)
    assert "nombre completo" in response.text.lower()
    
    # 3. Nombre
    request = IncomingMessageRequest(phone=phone, text="Juan Pérez")
    response = await use_case.execute(request)
    assert "dni" in response.text.lower()
    
    # 4. DNI
    request = IncomingMessageRequest(phone=phone, text="12345678")
    response = await use_case.execute(request)
    assert "fecha de nacimiento" in response.text.lower()
    
    # 5. Fecha de nacimiento
    request = IncomingMessageRequest(phone=phone, text="15/05/1985")
    response = await use_case.execute(request)
    assert "domicilio" in response.text.lower()
    
    # 6. Domicilio
    request = IncomingMessageRequest(phone=phone, text="San Martín 123, San Rafael, Mendoza")
    response = await use_case.execute(request)
    assert "datos personales completos" in response.text.lower()
    assert "documentación" in response.text.lower()

@pytest.mark.asyncio
async def test_validation_errors_dni(test_db):
    """Test de validación de DNI inválido"""
    use_case = ProcessIncomingMessageUseCase(test_db)
    phone = "+5492604123457"
    
    # Avanzar hasta fase DNI
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Hola"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="unilateral"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="María López"))
    
    # DNI inválido
    response = await use_case.execute(IncomingMessageRequest(phone=phone, text="abc123"))
    assert "dni válido" in response.text.lower()
    assert "dígitos" in response.text.lower()

@pytest.mark.asyncio
async def test_validation_errors_fecha_nacimiento(test_db):
    """Test de validación de fecha de nacimiento inválida"""
    use_case = ProcessIncomingMessageUseCase(test_db)
    phone = "+5492604123458"
    
    # Avanzar hasta fase fecha_nacimiento
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Hola"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="conjunta"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Carlos González"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="87654321"))
    
    # Menor de 18 años
    response = await use_case.execute(IncomingMessageRequest(phone=phone, text="01/01/2010"))
    assert not response.text.startswith("✅")
    assert "mayor de 18" in response.text.lower() or "válida" in response.text.lower()

@pytest.mark.asyncio
async def test_validation_address_jurisdiction(test_db):
    """Test de validación de jurisdicción en domicilio"""
    use_case = ProcessIncomingMessageUseCase(test_db)
    phone = "+5492604123459"
    
    # Avanzar hasta fase domicilio
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Hola"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="unilateral"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Ana Martínez"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="11223344"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="10/10/1980"))
    
    # Domicilio válido en San Rafael
    response = await use_case.execute(
        IncomingMessageRequest(phone=phone, text="Av. Libertador 500, San Rafael, Mendoza")
    )
    assert "datos personales completos" in response.text.lower()

@pytest.mark.asyncio
async def test_joke_response_detection(test_db):
    """Test de detección de respuestas no serias"""
    use_case = ProcessIncomingMessageUseCase(test_db)
    phone = "+5492604123460"
    
    # Avanzar hasta nombre
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Hola"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="unilateral"))
    
    # Respuesta jocosa
    response = await use_case.execute(IncomingMessageRequest(phone=phone, text="jajaja a molestar"))
    assert "nombre completo real" in response.text.lower() or "necesito" in response.text.lower()

@pytest.mark.asyncio
async def test_context_memory_persistence(test_db):
    """Test de que el contexto se mantiene entre mensajes"""
    use_case = ProcessIncomingMessageUseCase(test_db)
    phone = "+5492604123461"
    
    # Completar datos personales
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Hola"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="unilateral"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Pedro Sánchez"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="99887766"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="20/03/1975"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Belgrano 456, San Rafael, Mendoza"))
    
    # Ahora hacer una consulta general - debería tener contexto
    response = await use_case.execute(
        IncomingMessageRequest(phone=phone, text="¿Cuánto demora el trámite?")
    )
    
    # La respuesta debería ser relevante al divorcio
    assert len(response.text) > 0
    assert "error" not in response.text.lower()

@pytest.mark.asyncio
async def test_multiple_users_isolation(test_db):
    """Test de que múltiples usuarios mantienen sus propios contextos"""
    use_case = ProcessIncomingMessageUseCase(test_db)
    
    phone1 = "+5492604111111"
    phone2 = "+5492604222222"
    
    # Usuario 1 inicia
    response1 = await use_case.execute(IncomingMessageRequest(phone=phone1, text="Hola"))
    assert "tipo de divorcio" in response1.text.lower()
    
    # Usuario 2 inicia
    response2 = await use_case.execute(IncomingMessageRequest(phone=phone2, text="Hola"))
    assert "tipo de divorcio" in response2.text.lower()
    
    # Usuario 1 continúa
    response1 = await use_case.execute(IncomingMessageRequest(phone=phone1, text="unilateral"))
    assert "nombre completo" in response1.text.lower()
    
    # Usuario 2 elige otro tipo
    response2 = await use_case.execute(IncomingMessageRequest(phone=phone2, text="conjunta"))
    assert "nombre completo" in response2.text.lower()
    
    # Verificar que se guardaron tipos diferentes
    from infrastructure.persistence.repositories import CaseRepository
    cases_repo = CaseRepository(test_db)
    
    case1 = cases_repo.get_or_create_by_phone(phone1)
    case2 = cases_repo.get_or_create_by_phone(phone2)
    
    assert case1.type == "unilateral"
    assert case2.type == "conjunta"
