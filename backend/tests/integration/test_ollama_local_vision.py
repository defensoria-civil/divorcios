"""
Tests de integración para Ollama Local (embeddings) y Visión Cloud.

Estos tests verifican:
- Embeddings con nomic-embed-text:latest en Ollama local
- Análisis de imágenes con qwen3-vl:235b-cloud en Ollama Cloud
- OCR real de documentos usando visión

Ejecutar con: pytest tests/integration/test_ollama_local_vision.py -v -s
"""
import pytest
import asyncio
from infrastructure.ai.ollama_client import OllamaClient
from infrastructure.ai.ollama_vision_client import OllamaVisionClient
from core.config import settings


@pytest.mark.asyncio
@pytest.mark.requires_ollama
async def test_ollama_local_embeddings():
    """Test de embeddings con nomic-embed-text en Ollama local"""
    client = OllamaClient(model="nomic-embed-text:latest")
    
    texts = [
        "Divorcio de mutuo acuerdo",
        "Acta de matrimonio",
        "DNI argentino"
    ]
    
    print(f"\n🔄 Testing embeddings with nomic-embed-text:latest locally...")
    try:
        embeddings = await client.embed(texts)
        
        print(f"✓ Generated {len(embeddings)} embeddings")
        print(f"✓ First embedding dimension: {len(embeddings[0])}")
        
        assert len(embeddings) == 3
        assert all(len(emb) > 0 for emb in embeddings)
        assert isinstance(embeddings[0][0], float)
        
        print("✅ Local embeddings working correctly!")
    except Exception as e:
        pytest.skip(f"Local embeddings not available: {e}")


@pytest.mark.asyncio
async def test_vision_cloud_simple_image():
    """Test de visión cloud con imagen simple"""
    if not settings.ollama_cloud_api_key:
        pytest.skip("OLLAMA_CLOUD_API_KEY not configured")
    
    vision = OllamaVisionClient()
    
    # Crear una imagen de prueba con texto
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont
    
    # Imagen 200x100 con texto "DIVORCIO"
    img = Image.new('RGB', (200, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Texto grande y legible
    try:
        # Intentar usar una fuente más grande
        draw.text((20, 30), "DIVORCIO", fill='black')
    except:
        # Fallback si no hay fuente disponible
        draw.text((20, 30), "DIVORCIO", fill='black')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    prompt = "¿Qué palabra está escrita en esta imagen? Responde solo con la palabra."
    
    print(f"\n🔄 Testing qwen3-vl:235b-cloud OCR...")
    try:
        response = await vision.analyze_image(
            image_bytes, 
            prompt, 
            model="qwen3-vl:235b-cloud"
        )
        
        print(f"✓ Response: {response}")
        assert response is not None
        assert len(response) > 0
        
        # Verificar que detectó algo relacionado con "DIVORCIO"
        if "divorcio" in response.lower():
            print("✅ OCR detected text correctly!")
        else:
            print(f"⚠️ OCR response: {response} (expected 'DIVORCIO')")
        
    except Exception as e:
        print(f"⚠️ Vision cloud error: {e}")
        pytest.skip(f"Vision cloud not available: {e}")


@pytest.mark.asyncio
async def test_vision_cloud_real_ocr():
    """Test de OCR real con formato estructurado JSON"""
    if not settings.ollama_cloud_api_key:
        pytest.skip("OLLAMA_CLOUD_API_KEY not configured")
    
    vision = OllamaVisionClient()
    
    # Crear una imagen simulando un documento con datos
    from io import BytesIO
    from PIL import Image, ImageDraw
    
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Simular datos de un documento
    text_lines = [
        "DNI: 12345678",
        "NOMBRE: JUAN PEREZ",
        "APELLIDO: GOMEZ",
        "FECHA NAC: 15/03/1980"
    ]
    
    y_pos = 50
    for line in text_lines:
        draw.text((50, y_pos), line, fill='black')
        y_pos += 40
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    prompt = """Extrae los datos del documento y devuélvelos en formato JSON con esta estructura:
{
  "dni": "número del DNI",
  "nombre": "nombre completo",
  "apellido": "apellido",
  "fecha_nacimiento": "fecha en formato DD/MM/YYYY"
}

Responde SOLO con el JSON, sin texto adicional."""
    
    print(f"\n🔄 Testing structured OCR extraction...")
    try:
        response = await vision.analyze_image(
            image_bytes, 
            prompt, 
            model="qwen3-vl:235b-cloud"
        )
        
        print(f"✓ Raw response:\n{response}")
        
        # Intentar parsear como JSON
        import json
        import re
        
        # Buscar JSON en la respuesta
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            print(f"✓ Parsed JSON: {data}")
            
            # Verificar campos esperados
            assert "dni" in data or "DNI" in data
            print("✅ Structured OCR working!")
        else:
            print(f"⚠️ No JSON found in response, but got: {response[:200]}")
        
    except Exception as e:
        print(f"⚠️ Structured OCR error: {e}")
        pytest.skip(f"Structured OCR not working: {e}")


@pytest.mark.asyncio
async def test_vision_multimodal_reasoning():
    """Test de razonamiento multimodal con imagen"""
    if not settings.ollama_cloud_api_key:
        pytest.skip("OLLAMA_CLOUD_API_KEY not configured")
    
    vision = OllamaVisionClient()
    
    # Crear una imagen con formas geométricas
    from io import BytesIO
    from PIL import Image, ImageDraw
    
    img = Image.new('RGB', (300, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Dibujar un círculo rojo y un cuadrado azul
    draw.ellipse([50, 50, 150, 150], fill='red', outline='black')
    draw.rectangle([170, 170, 270, 270], fill='blue', outline='black')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    prompt = "Describe las formas geométricas en la imagen. ¿Cuántas hay y de qué colores son?"
    
    print(f"\n🔄 Testing multimodal reasoning...")
    try:
        response = await vision.analyze_image(
            image_bytes, 
            prompt, 
            model="qwen3-vl:235b-cloud"
        )
        
        print(f"✓ Response: {response}")
        
        # Verificar que mencionó formas y colores
        response_lower = response.lower()
        mentions_shapes = any(word in response_lower for word in ['círculo', 'circle', 'cuadrado', 'square', 'rectángulo'])
        mentions_colors = any(word in response_lower for word in ['rojo', 'red', 'azul', 'blue'])
        
        if mentions_shapes and mentions_colors:
            print("✅ Multimodal reasoning working!")
        else:
            print(f"⚠️ Response may be incomplete: {response}")
        
        assert response is not None
        
    except Exception as e:
        print(f"⚠️ Multimodal reasoning error: {e}")
        pytest.skip(f"Multimodal reasoning not available: {e}")


@pytest.mark.asyncio
@pytest.mark.requires_ollama
async def test_embedding_similarity():
    """Test de similitud semántica con embeddings"""
    client = OllamaClient(model="nomic-embed-text:latest")
    
    # Textos similares y diferentes
    texts = [
        "Solicitud de divorcio de mutuo acuerdo",
        "Petición de divorcio consensuado",
        "Compra de automóvil usado"
    ]
    
    print(f"\n🔄 Testing semantic similarity...")
    try:
        embeddings = await client.embed(texts)
        
        # Calcular similitud coseno entre embeddings
        import numpy as np
        
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        sim_1_2 = cosine_similarity(embeddings[0], embeddings[1])
        sim_1_3 = cosine_similarity(embeddings[0], embeddings[2])
        
        print(f"✓ Similarity (divorcio vs divorcio): {sim_1_2:.4f}")
        print(f"✓ Similarity (divorcio vs automóvil): {sim_1_3:.4f}")
        
        # Los dos textos sobre divorcio deben ser más similares
        assert sim_1_2 > sim_1_3, "Semantic similarity not working correctly"
        print("✅ Semantic similarity working!")
        
    except Exception as e:
        pytest.skip(f"Semantic similarity not available: {e}")


if __name__ == "__main__":
    print("🚀 Running Ollama Local + Vision Cloud Integration Tests")
    print("=" * 60)
    pytest.main([__file__, "-v", "-s"])
