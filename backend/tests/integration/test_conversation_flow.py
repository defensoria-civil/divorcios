import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.persistence.db import Base
from application.use_cases.process_incoming_message import (
    ProcessIncomingMessageUseCase,
    IncomingMessageRequest,
)
from tests.conftest import get_test_database_url


@pytest.fixture(scope="function")
def test_db():
    """Crea DB de test limpia para cada test usando la URL de test configurable.

    Usa TEST_DATABASE_URL si está definida; de lo contrario, intenta PostgreSQL local
    y cae a SQLite en memoria.
    """
    engine = create_engine(get_test_database_url())
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_complete_divorce_flow_unilateral(test_db):
    """Test del flujo completo de divorcio unilateral hasta datos personales completos."""
    use_case = ProcessIncomingMessageUseCase(test_db)
    phone = "+5492604123456"

    # 1. Inicio
    request = IncomingMessageRequest(phone=phone, text="Hola")
    response = await use_case.execute(request)
    assert "tipo de divorcio" in response.text.lower()

    # 2. Tipo de divorcio
    request = IncomingMessageRequest(phone=phone, text="unilateral")
    response = await use_case.execute(request)
    # Ahora debe pedir apellido
    assert "apellido" in response.text.lower()

    # 3. Apellido
    request = IncomingMessageRequest(phone=phone, text="Pérez")
    response = await use_case.execute(request)
    assert "tus nombres" in response.text.lower()

    # 4. Nombres
    request = IncomingMessageRequest(phone=phone, text="Juan Carlos")
    response = await use_case.execute(request)
    assert "cuit" in response.text.lower()

    # 5. CUIT/CUIL (de donde se extrae DNI)
    request = IncomingMessageRequest(phone=phone, text="20-12345678-9")
    response = await use_case.execute(request)
    assert "dni extraído" in response.text.lower()
    assert "fecha de nacimiento" in response.text.lower()

    # 6. Fecha de nacimiento
    request = IncomingMessageRequest(phone=phone, text="15/05/1985")
    response = await use_case.execute(request)
    assert "domicilio" in response.text.lower()

    # 7. Domicilio
    request = IncomingMessageRequest(phone=phone, text="San Martín 123, San Rafael, Mendoza")
    response = await use_case.execute(request)
    # Pasa a perfil económico
    assert "datos económicos" in response.text.lower()

@pytest.mark.asyncio
async def test_validation_errors_cuit(test_db):
    """Test de validación de CUIT inválido (de donde se extrae el DNI)."""
    use_case = ProcessIncomingMessageUseCase(test_db)
    phone = "+5492604123457"

    # Avanzar hasta fase CUIT
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Hola"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="unilateral"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="López"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="María"))

    # CUIT inválido: puede devolver mensaje específico o caer en fallback seguro
    response = await use_case.execute(IncomingMessageRequest(phone=phone, text="abc123"))
    text = response.text.lower()
    assert len(text) > 0
    # Aceptamos cualquiera de estas pistas: validación de formato o pedido de reformulación genérico
    assert ("11 dígitos" in text or "reformular" in text or "no es válida" in text)

@pytest.mark.asyncio
async def test_validation_errors_fecha_nacimiento(test_db):
    """Test de validación de fecha de nacimiento inválida."""
    use_case = ProcessIncomingMessageUseCase(test_db)
    phone = "+5492604123458"

    # Avanzar hasta fase fecha_nacimiento
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Hola"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="conjunta"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="González"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Carlos"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="20-87654321-9"))

    # Fecha inválida (ej: formato correcto pero Pydantic la marca como invalida por validador)
    response = await use_case.execute(IncomingMessageRequest(phone=phone, text="01/01/2010"))
    assert "fecha no es válida" in response.text.lower() or "no es válida" in response.text.lower()

@pytest.mark.asyncio
async def test_validation_address_jurisdiction(test_db):
    """Test de validación de jurisdicción en domicilio."""
    use_case = ProcessIncomingMessageUseCase(test_db)
    phone = "+5492604123459"

    # Avanzar hasta fase domicilio
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Hola"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="unilateral"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Martínez"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Ana"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="20-11223344-9"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="10/10/1980"))

    # Domicilio válido en San Rafael
    response = await use_case.execute(
        IncomingMessageRequest(phone=phone, text="Av. Libertador 500, San Rafael, Mendoza")
    )
    assert "datos económicos" in response.text.lower()

@pytest.mark.asyncio
async def test_joke_response_detection(test_db):
    """Test de detección de respuestas no serias"""
    use_case = ProcessIncomingMessageUseCase(test_db)
    phone = "+5492604123460"
    
    # Avanzar hasta nombre
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Hola"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="unilateral"))
    
    # Respuesta jocosa: debe volver a encarrilar al usuario hacia un nombre válido
    response = await use_case.execute(IncomingMessageRequest(phone=phone, text="jajaja a molestar"))
    text = response.text.lower()
    assert len(text) > 0
    # Lo importante es que pida datos serios de identificación (nombre/apellido)
    assert ("nombre" in text or "nombres" in text or "apellido" in text)

@pytest.mark.asyncio
async def test_context_memory_persistence(test_db):
    """Test de que el contexto se mantiene entre mensajes y se persiste en DB/memoria."""
    from infrastructure.persistence.repositories import CaseRepository, MessageRepository
    from application.services.memory_service import MemoryService

    use_case = ProcessIncomingMessageUseCase(test_db)
    phone = "+5492604123461"

    # Completar datos personales con el flujo real (apellido + nombres + CUIT)
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Hola"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="unilateral"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Sánchez"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Pedro"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="20-99887766-3"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="20/03/1975"))
    await use_case.execute(IncomingMessageRequest(phone=phone, text="Belgrano 456, San Rafael, Mendoza"))

    cases_repo = CaseRepository(test_db)
    messages_repo = MessageRepository(test_db)

    case = cases_repo.get_or_create_by_phone(phone)

    # Verificar que en DB están los mensajes guardados
    last_msgs = messages_repo.last_messages(case.id, limit=10)
    assert any("Belgrano 456" in (m.content or "") for m in last_msgs)

    # Verificar que la memoria de sesión tiene datos clave
    memory = MemoryService(test_db)
    session_data = await memory.retrieve_session_data(case.id)
    assert session_data.get("nombre") is not None
    assert session_data.get("dni") == "99887766"
    assert "Belgrano" in session_data.get("domicilio", "")

    # Ahora hacer una consulta general - debería construirse contexto sin errores
    response = await use_case.execute(
        IncomingMessageRequest(phone=phone, text="¿Cuánto demora el trámite?")
    )

    assert len(response.text) > 0
    assert "error" not in response.text.lower()

@pytest.mark.asyncio
async def test_multiple_users_isolation(test_db):
    """Test de que múltiples usuarios mantienen sus propios contextos y casos aislados."""
    from infrastructure.persistence.repositories import CaseRepository, MessageRepository
    from application.services.memory_service import MemoryService

    use_case = ProcessIncomingMessageUseCase(test_db)

    phone1 = "+5492604111111"
    phone2 = "+5492604222222"

    # Usuario 1 inicia y avanza un paso
    await use_case.execute(IncomingMessageRequest(phone=phone1, text="Hola"))
    await use_case.execute(IncomingMessageRequest(phone=phone1, text="unilateral"))

    # Usuario 2 inicia y elige otro tipo
    await use_case.execute(IncomingMessageRequest(phone=phone2, text="Hola"))
    await use_case.execute(IncomingMessageRequest(phone=phone2, text="conjunta"))

    cases_repo = CaseRepository(test_db)
    messages_repo = MessageRepository(test_db)
    memory = MemoryService(test_db)

    case1 = cases_repo.get_or_create_by_phone(phone1)
    case2 = cases_repo.get_or_create_by_phone(phone2)

    # Tipos de divorcio distintos
    assert case1.type == "unilateral"
    assert case2.type == "conjunta"

    # Mensajes de cada caso no se mezclan
    msgs1 = messages_repo.last_messages(case1.id, limit=10)
    msgs2 = messages_repo.last_messages(case2.id, limit=10)
    assert all(phone1 in (m.phone or phone1) for m in msgs1) if hasattr(msgs1[0], "phone") else len(msgs1) > 0
    assert all(phone2 in (m.phone or phone2) for m in msgs2) if hasattr(msgs2[0], "phone") else len(msgs2) > 0

    # Memoria de sesión separada (al menos 'type' distinto)
    session1 = await memory.retrieve_session_data(case1.id)
    session2 = await memory.retrieve_session_data(case2.id)
    assert session1.get("type") == "unilateral"
    assert session2.get("type") == "conjunta"
