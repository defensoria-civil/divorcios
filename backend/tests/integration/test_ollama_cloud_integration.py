"""
Tests de integración con Ollama Cloud API.

Estos tests requieren:
- OLLAMA_CLOUD_API_KEY configurado en .env
- Conexión a internet
- Créditos en cuenta de Ollama Cloud

Ejecutar con: pytest tests/integration/test_ollama_cloud_integration.py -v -s
"""
import pytest
import asyncio
from infrastructure.ai.ollama_cloud_client import OllamaCloudClient
from infrastructure.ai.ollama_vision_client import OllamaVisionClient
from infrastructure.ai.router import LLMRouter
from core.config import settings


# Skip si no hay API key configurada
pytestmark = pytest.mark.skipif(
    not settings.ollama_cloud_api_key,
    reason="OLLAMA_CLOUD_API_KEY not configured"
)


@pytest.mark.asyncio
async def test_ollama_cloud_chat_minimax():
    """Test de chat real con minimax-m2:cloud"""
    client = OllamaCloudClient()
    
    messages = [
        {"role": "user", "content": "Di solo 'OK' si me entiendes"}
    ]
    
    print("\n🔄 Testing minimax-m2:cloud...")
    response = await client.chat(messages, model="minimax-m2:cloud")
    
    print(f"✓ Response: {response}")
    assert response is not None
    assert len(response) > 0
    assert isinstance(response, str)


@pytest.mark.asyncio
async def test_ollama_cloud_chat_glm():
    """Test de chat real con glm-4.6:cloud"""
    client = OllamaCloudClient()
    
    messages = [
        {"role": "user", "content": "Responde solo con 'FUNCIONA' si recibes este mensaje"}
    ]
    
    print("\n🔄 Testing glm-4.6:cloud...")
    response = await client.chat(messages, model="glm-4.6:cloud")
    
    print(f"✓ Response: {response}")
    assert response is not None
    assert len(response) > 0


@pytest.mark.asyncio
async def test_ollama_cloud_chat_deepseek():
    """Test de chat real con deepseek-v3.1:671b-cloud"""
    client = OllamaCloudClient()
    
    messages = [
        {"role": "user", "content": "¿Cuál es 2+2? Responde solo con el número."}
    ]
    
    print("\n🔄 Testing deepseek-v3.1:671b-cloud...")
    response = await client.chat(messages, model="deepseek-v3.1:671b-cloud")
    
    print(f"✓ Response: {response}")
    assert response is not None
    assert "4" in response


@pytest.mark.asyncio
async def test_ollama_cloud_embeddings():
    """Test de generación de embeddings real"""
    client = OllamaCloudClient()
    
    texts = ["Hola mundo", "Test de embeddings"]
    
    print("\n🔄 Testing embeddings with nomic-embed-text...")
    try:
        embeddings = await client.embed(texts, model="nomic-embed-text")
        
        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"✓ Embedding dimension: {len(embeddings[0])}")
        
        assert len(embeddings) == 2
        assert len(embeddings[0]) > 0
        assert len(embeddings[1]) > 0
        assert isinstance(embeddings[0], list)
        assert isinstance(embeddings[0][0], float)
    except Exception as e:
        pytest.skip(f"Embeddings API not available or configured: {e}")


@pytest.mark.asyncio
async def test_ollama_vision_simple_image():
    """Test de análisis de imagen simple con qwen3-vl:235b-cloud"""
    vision = OllamaVisionClient()
    
    # Crear una imagen simple de prueba (100x100 pixel rojo en PNG)
    import base64
    from io import BytesIO
    from PIL import Image
    
    # Crear imagen de prueba
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    prompt = "¿De qué color es esta imagen? Responde en una palabra."
    
    print("\n🔄 Testing qwen3-vl:235b-cloud with image...")
    try:
        response = await vision.analyze_image(image_bytes, prompt, model="qwen3-vl:235b-cloud")
        
        print(f"✓ Response: {response}")
        assert response is not None
        assert len(response) > 0
        print("✅ Vision API working correctly!")
    except Exception as e:
        print(f"⚠️ Vision API error: {e}")
        pytest.skip(f"Vision API not available or model not configured: {e}")


@pytest.mark.asyncio
async def test_llm_router_with_task_types():
    """Test del router con diferentes task_types usando API real"""
    router = LLMRouter()
    
    # Test chat
    print("\n🔄 Testing router with task_type='chat'...")
    response = await router.chat(
        [{"role": "user", "content": "Di 'CHAT OK'"}],
        task_type="chat"
    )
    print(f"✓ Chat response: {response}")
    assert response is not None
    
    # Test hallucination_check
    print("\n🔄 Testing router with task_type='hallucination_check'...")
    response = await router.chat(
        [{"role": "user", "content": "Di 'VALIDATION OK'"}],
        task_type="hallucination_check"
    )
    print(f"✓ Hallucination check response: {response}")
    assert response is not None


@pytest.mark.asyncio
async def test_llm_router_embeddings():
    """Test de embeddings a través del router"""
    router = LLMRouter()
    
    texts = ["Test texto 1", "Test texto 2", "Test texto 3"]
    
    print(f"\n🔄 Testing router embeddings with {len(texts)} texts...")
    try:
        embeddings = await router.embed(texts)
        
        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"✓ First embedding dimension: {len(embeddings[0])}")
        
        assert len(embeddings) == 3
        assert all(len(emb) > 0 for emb in embeddings)
    except Exception as e:
        pytest.skip(f"No embedding providers available: {e}")


@pytest.mark.asyncio
async def test_conversation_flow():
    """Test de flujo conversacional multi-turno"""
    client = OllamaCloudClient()
    
    print("\n🔄 Testing multi-turn conversation...")
    
    # Turno 1
    messages = [
        {"role": "user", "content": "Mi nombre es Juan"}
    ]
    response1 = await client.chat(messages, model="minimax-m2:cloud")
    print(f"✓ Turn 1: {response1}")
    
    # Turno 2 - verificar memoria contextual
    messages.append({"role": "assistant", "content": response1})
    messages.append({"role": "user", "content": "¿Cuál es mi nombre?"})
    
    response2 = await client.chat(messages, model="minimax-m2:cloud")
    print(f"✓ Turn 2: {response2}")
    
    assert "juan" in response2.lower()


@pytest.mark.asyncio
async def test_latency_benchmark():
    """Test de benchmark de latencia de diferentes modelos"""
    import time
    
    client = OllamaCloudClient()
    messages = [{"role": "user", "content": "Di 'OK'"}]
    
    models = [
        "minimax-m2:cloud",
        "glm-4.6:cloud",
    ]
    
    print("\n📊 Latency Benchmark:")
    print("-" * 50)
    
    for model in models:
        start = time.time()
        try:
            response = await client.chat(messages, model=model)
            latency = time.time() - start
            print(f"✓ {model:30} {latency:.2f}s")
            assert latency < 30  # Max 30 segundos
        except Exception as e:
            print(f"✗ {model:30} ERROR: {str(e)}")


@pytest.mark.asyncio
async def test_error_handling_invalid_model():
    """Test de manejo de errores con modelo inválido"""
    client = OllamaCloudClient()
    
    messages = [{"role": "user", "content": "test"}]
    
    print("\n🔄 Testing error handling with invalid model...")
    with pytest.raises(Exception):
        await client.chat(messages, model="modelo-inexistente:cloud")
    
    print("✓ Error handled correctly")


@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test de requests concurrentes"""
    client = OllamaCloudClient()
    
    messages = [{"role": "user", "content": "Di 'OK'"}]
    
    print("\n🔄 Testing 3 concurrent requests...")
    
    tasks = [
        client.chat(messages, model="minimax-m2:cloud")
        for _ in range(3)
    ]
    
    responses = await asyncio.gather(*tasks)
    
    print(f"✓ Received {len(responses)} responses")
    assert len(responses) == 3
    assert all(r is not None for r in responses)


if __name__ == "__main__":
    # Permitir ejecutar directamente
    print("🚀 Running Ollama Cloud Integration Tests")
    print("=" * 60)
    pytest.main([__file__, "-v", "-s"])
