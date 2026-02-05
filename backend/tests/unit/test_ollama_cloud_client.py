import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from infrastructure.ai.ollama_cloud_client import OllamaCloudClient


@pytest.fixture
def mock_settings():
    """Mock de settings para tests"""
    with patch('infrastructure.ai.ollama_cloud_client.settings') as mock:
        mock.ollama_cloud_base_url = "https://ollama.com"
        mock.ollama_cloud_api_key = "test_api_key"
        mock.llm_chat_model = "minimax-m2:cloud"
        yield mock


@pytest.fixture
def client(mock_settings):
    """Cliente con configuración mockeada"""
    return OllamaCloudClient()


@pytest.mark.asyncio
async def test_chat_success(client):
    """Test de chat exitoso con respuesta válida"""
    messages = [{"role": "user", "content": "Hola"}]
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"content": "Hola, ¿cómo puedo ayudarte?"}
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        
        response = await client.chat(messages)
        
        assert response == "Hola, ¿cómo puedo ayudarte?"
        assert mock_client.return_value.__aenter__.return_value.post.called


@pytest.mark.asyncio
async def test_chat_with_specific_model(client):
    """Test de chat con modelo específico"""
    messages = [{"role": "user", "content": "Test"}]
    model = "glm-4.6:cloud"
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"content": "Response"}
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post
        
        response = await client.chat(messages, model=model)
        
        # Verificar que se llamó con el modelo correcto
        call_args = mock_post.call_args
        assert call_args[1]['json']['model'] == model


@pytest.mark.asyncio
async def test_chat_with_tools(client):
    """Test de chat con tools para function calling"""
    messages = [{"role": "user", "content": "Test"}]
    tools = [{"type": "function", "function": {"name": "get_weather"}}]
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"content": "Using tool"}
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post
        
        response = await client.chat(messages, tools=tools)
        
        # Verificar que se pasaron los tools
        call_args = mock_post.call_args
        assert 'tools' in call_args[1]['json']
        assert call_args[1]['json']['tools'] == tools


@pytest.mark.asyncio
async def test_chat_timeout(client):
    """Test de manejo de timeout"""
    messages = [{"role": "user", "content": "Test"}]
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=Exception("Timeout")
        )
        
        with pytest.raises(Exception):
            await client.chat(messages)


@pytest.mark.asyncio
async def test_chat_http_error(client):
    """Test de manejo de errores HTTP"""
    messages = [{"role": "user", "content": "Test"}]
    
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("HTTP 500")
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        
        with pytest.raises(Exception):
            await client.chat(messages)


@pytest.mark.asyncio
async def test_embed_success(client):
    """Test de generación de embeddings exitosa"""
    texts = ["texto 1", "texto 2"]
    
    mock_response_1 = MagicMock()
    mock_response_1.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    mock_response_1.raise_for_status = MagicMock()
    
    mock_response_2 = MagicMock()
    mock_response_2.json.return_value = {"embedding": [0.4, 0.5, 0.6]}
    mock_response_2.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=[mock_response_1, mock_response_2]
        )
        
        embeddings = await client.embed(texts)
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]


@pytest.mark.asyncio
async def test_embed_with_custom_model(client):
    """Test de embeddings con modelo personalizado"""
    texts = ["test"]
    custom_model = "custom-embed-model"
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"embedding": [0.1]}
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = mock_post
        
        await client.embed(texts, model=custom_model)
        
        # Verificar que se usó el modelo correcto
        call_args = mock_post.call_args
        assert call_args[1]['json']['model'] == custom_model


def test_headers_include_auth(client):
    """Test de que los headers incluyen autenticación"""
    headers = client._headers()
    
    assert 'Authorization' in headers
    assert headers['Authorization'] == 'Bearer test_api_key'
    assert headers['Content-Type'] == 'application/json'


def test_client_initialization(mock_settings):
    """Test de inicialización correcta del cliente"""
    client = OllamaCloudClient()
    
    assert client.base_url == "https://ollama.com"
    assert client.api_key == "test_api_key"
    assert client.timeout == 120
    assert client.default_chat_model == "minimax-m2:cloud"
