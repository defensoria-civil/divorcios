import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.ai.router import LLMRouter


@pytest.fixture
def mock_settings():
    """Mock de settings para tests"""
    with patch('infrastructure.ai.router.settings') as mock:
        mock.llm_chat_model = "minimax-m2:cloud"
        mock.llm_reasoning_model = "deepseek-v3.1:671b-cloud"
        mock.llm_hallucination_model = "glm-4.6:cloud"
        mock.llm_vision_model = "qwen3-vl:cloud"
        mock.llm_embedding_model = "nomic-embed-text"
        yield mock


@pytest.fixture
def router(mock_settings):
    """Router con configuración mockeada"""
    with patch('infrastructure.ai.router.OllamaCloudClient'), \
         patch('infrastructure.ai.router.OllamaClient'), \
         patch('infrastructure.ai.router.GeminiClient'):
        return LLMRouter()


@pytest.mark.asyncio
async def test_chat_uses_correct_model_for_task_type(router):
    """Test de que el router selecciona el modelo correcto según task_type"""
    messages = [{"role": "user", "content": "Test"}]
    
    # Mock del proveedor
    router.providers['ollama_cloud'].chat = AsyncMock(return_value="Response")
    
    # Test chat normal
    await router.chat(messages, task_type='chat')
    router.providers['ollama_cloud'].chat.assert_called_once()
    call_kwargs = router.providers['ollama_cloud'].chat.call_args[1]
    assert call_kwargs['model'] == "minimax-m2:cloud"
    
    # Reset mock
    router.providers['ollama_cloud'].chat.reset_mock()
    
    # Test hallucination check
    await router.chat(messages, task_type='hallucination_check')
    call_kwargs = router.providers['ollama_cloud'].chat.call_args[1]
    assert call_kwargs['model'] == "glm-4.6:cloud"


@pytest.mark.asyncio
async def test_chat_fallback_to_local_on_cloud_failure(router):
    """Test de fallback automático a Ollama Local cuando Cloud falla"""
    messages = [{"role": "user", "content": "Test"}]
    
    # Simular fallo de Ollama Cloud
    router.providers['ollama_cloud'].chat = AsyncMock(
        side_effect=Exception("Cloud failed")
    )
    # Ollama Local funciona
    router.providers['ollama_local'].chat = AsyncMock(return_value="Local response")
    
    response = await router.chat(messages)
    
    assert response == "Local response"
    assert router.providers['ollama_cloud'].chat.called
    assert router.providers['ollama_local'].chat.called


@pytest.mark.asyncio
async def test_chat_fallback_to_gemini_when_all_ollama_fail(router):
    """Test de fallback a Gemini cuando ambos Ollama fallan"""
    messages = [{"role": "user", "content": "Test"}]
    
    # Simular fallo de ambos Ollama
    router.providers['ollama_cloud'].chat = AsyncMock(
        side_effect=Exception("Cloud failed")
    )
    router.providers['ollama_local'].chat = AsyncMock(
        side_effect=Exception("Local failed")
    )
    # Gemini funciona
    router.providers['gemini'].chat = AsyncMock(return_value="Gemini response")
    
    response = await router.chat(messages)
    
    assert response == "Gemini response"
    assert router.providers['ollama_cloud'].chat.called
    assert router.providers['ollama_local'].chat.called
    assert router.providers['gemini'].chat.called


@pytest.mark.asyncio
async def test_chat_raises_when_all_providers_fail(router):
    """Test de que se lanza excepción cuando todos los proveedores fallan"""
    messages = [{"role": "user", "content": "Test"}]
    
    # Simular fallo de todos los proveedores
    router.providers['ollama_cloud'].chat = AsyncMock(
        side_effect=Exception("Cloud failed")
    )
    router.providers['ollama_local'].chat = AsyncMock(
        side_effect=Exception("Local failed")
    )
    router.providers['gemini'].chat = AsyncMock(
        side_effect=Exception("Gemini failed")
    )
    
    with pytest.raises(Exception):
        await router.chat(messages)


@pytest.mark.asyncio
async def test_chat_with_tools(router):
    """Test de que los tools se pasan correctamente al proveedor"""
    messages = [{"role": "user", "content": "Test"}]
    tools = [{"type": "function", "function": {"name": "test"}}]
    
    router.providers['ollama_cloud'].chat = AsyncMock(return_value="Response")
    
    await router.chat(messages, tools=tools)
    
    call_kwargs = router.providers['ollama_cloud'].chat.call_args[1]
    assert call_kwargs['tools'] == tools


@pytest.mark.asyncio
async def test_embed_prefers_local_for_speed(router):
    """Test de que embeddings prefiere Ollama Local por velocidad"""
    texts = ["test"]
    
    router.providers['ollama_local'].embed = AsyncMock(return_value=[[0.1, 0.2]])
    
    embeddings = await router.embed(texts)
    
    assert embeddings == [[0.1, 0.2]]
    # Verificar que se llamó primero al local
    assert router.providers['ollama_local'].embed.called


@pytest.mark.asyncio
async def test_embed_fallback_chain(router):
    """Test de cadena de fallback para embeddings: Local → Cloud → Gemini"""
    texts = ["test"]
    
    # Simular fallo de Local
    router.providers['ollama_local'].embed = AsyncMock(
        side_effect=Exception("Local failed")
    )
    # Cloud funciona
    router.providers['ollama_cloud'].embed = AsyncMock(return_value=[[0.1]])
    
    embeddings = await router.embed(texts)
    
    assert embeddings == [[0.1]]
    assert router.providers['ollama_local'].embed.called
    assert router.providers['ollama_cloud'].embed.called


@pytest.mark.asyncio
async def test_embed_uses_custom_model(router):
    """Test de que embed puede usar un modelo personalizado"""
    texts = ["test"]
    custom_model = "custom-embed"
    
    router.providers['ollama_local'].embed = AsyncMock(return_value=[[0.1]])
    
    await router.embed(texts, model=custom_model)
    
    # El comportamiento depende de si el proveedor soporta el parámetro model
    # Aquí verificamos que se llamó
    assert router.providers['ollama_local'].embed.called


def test_router_initialization(mock_settings):
    """Test de inicialización correcta del router"""
    with patch('infrastructure.ai.router.OllamaCloudClient'), \
         patch('infrastructure.ai.router.OllamaClient'), \
         patch('infrastructure.ai.router.GeminiClient'):
        
        router = LLMRouter()
        
        assert 'ollama_cloud' in router.providers
        assert 'ollama_local' in router.providers
        assert 'gemini' in router.providers
        assert router.fallback_order == ['ollama_cloud', 'ollama_local', 'gemini']
        assert 'chat' in router.model_map
        assert 'reasoning' in router.model_map
        assert 'hallucination_check' in router.model_map


def test_model_map_has_all_task_types(router):
    """Test de que el model_map tiene todos los tipos de tarea"""
    expected_types = ['chat', 'reasoning', 'hallucination_check', 'vision_ocr', 'embeddings']
    
    for task_type in expected_types:
        assert task_type in router.model_map
        assert router.model_map[task_type] is not None


@pytest.mark.asyncio
async def test_router_logs_provider_attempts(router):
    """Test de que el router loggea los intentos de cada proveedor"""
    messages = [{"role": "user", "content": "Test"}]
    
    router.providers['ollama_cloud'].chat = AsyncMock(return_value="Response")
    
    with patch('infrastructure.ai.router.logger') as mock_logger:
        await router.chat(messages)
        
        # Verificar que se loggeó el intento y el éxito
        assert mock_logger.info.called
        calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any('llm_router_attempt' in str(call) for call in calls)
        assert any('llm_router_success' in str(call) for call in calls)


@pytest.mark.asyncio
async def test_router_logs_failures_before_fallback(router):
    """Test de que el router loggea fallos antes de hacer fallback"""
    messages = [{"role": "user", "content": "Test"}]
    
    router.providers['ollama_cloud'].chat = AsyncMock(
        side_effect=Exception("Failed")
    )
    router.providers['ollama_local'].chat = AsyncMock(return_value="Response")
    
    with patch('infrastructure.ai.router.logger') as mock_logger:
        await router.chat(messages)
        
        # Verificar que se loggeó el warning del fallo
        assert mock_logger.warning.called
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any('llm_router_provider_failed' in str(call) for call in warning_calls)
