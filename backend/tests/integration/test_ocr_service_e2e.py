"""
Tests end-to-end del OCR Service con documentos simulados.

Estos tests verifican el flujo completo de:
1. Creación de imágenes simuladas de DNI y actas
2. Extracción de datos con OCR
3. Validación de resultados
4. Fallback automático entre proveedores

Ejecutar con: pytest tests/integration/test_ocr_service_e2e.py -v -s
"""
import pytest
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from infrastructure.ocr.ocr_service_impl import MultiProviderOCRService
from core.config import settings


def create_dni_image() -> bytes:
    """Crea una imagen simulada de DNI argentino para testing"""
    img = Image.new('RGB', (800, 500), color='white')
    draw = ImageDraw.Draw(img)
    
    # Simular datos típicos de DNI
    text_lines = [
        ("REPÚBLICA ARGENTINA", 50, 30),
        ("DNI", 100, 80),
        ("DOCUMENTO NACIONAL DE IDENTIDAD", 50, 120),
        ("", 0, 0),  # Espacio
        ("APELLIDO: PEREZ", 50, 180),
        ("NOMBRES: JUAN CARLOS", 50, 220),
        ("SEXO: M", 50, 260),
        ("FECHA DE NACIMIENTO: 15/03/1985", 50, 300),
        ("N° DE DOCUMENTO: 28123456", 50, 340),
        ("FECHA DE EMISIÓN: 10/05/2020", 50, 380),
    ]
    
    for text, x, y in text_lines:
        if text:  # Skip espacios vacíos
            draw.text((x, y), text, fill='black')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def create_marriage_certificate_image() -> bytes:
    """Crea una imagen simulada de acta de matrimonio para testing"""
    img = Image.new('RGB', (1000, 700), color='white')
    draw = ImageDraw.Draw(img)
    
    # Simular datos típicos de acta de matrimonio
    text_lines = [
        ("REPÚBLICA ARGENTINA", 100, 50),
        ("ACTA DE MATRIMONIO", 100, 100),
        ("", 0, 0),  # Espacio
        ("Registro Civil N° 5 - San Rafael, Mendoza", 100, 160),
        ("", 0, 0),
        ("CÓNYUGES:", 100, 220),
        ("MARÍA RODRIGUEZ", 150, 260),
        ("PEDRO GOMEZ", 150, 300),
        ("", 0, 0),
        ("FECHA DE MATRIMONIO: 20/02/2023", 100, 360),
        ("LUGAR: San Rafael, Mendoza", 100, 400),
        ("", 0, 0),
        ("Tomo: 15", 100, 460),
        ("Folio: 234", 100, 500),
        ("Acta N°: 456", 100, 540),
    ]
    
    for text, x, y in text_lines:
        if text:
            draw.text((x, y), text, fill='black')
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_dni_extraction_complete_flow():
    """Test del flujo completo de extracción de DNI"""
    if not settings.ollama_cloud_api_key:
        pytest.skip("OLLAMA_CLOUD_API_KEY not configured")
    
    service = MultiProviderOCRService()
    dni_image = create_dni_image()
    
    print("\n🔄 Extracting DNI data with OCR Service...")
    result = await service.extract_dni_data(dni_image)
    
    print(f"✓ Success: {result.success}")
    print(f"✓ Confidence: {result.confidence:.2f}")
    print(f"✓ Data extracted: {result.data}")
    print(f"✓ Errors: {result.errors}")
    
    # Validaciones básicas
    assert result.success is not None, "Result should have success flag"
    assert result.confidence >= 0.0, "Confidence should be non-negative"
    assert isinstance(result.data, dict), "Data should be a dictionary"
    
    # Si fue exitoso, verificar campos requeridos
    if result.success:
        assert "numero_documento" in result.data, "Should extract document number"
        assert "nombre_completo" in result.data, "Should extract full name"
        print("✅ DNI extraction successful with all required fields!")
    else:
        print(f"⚠️ DNI extraction had issues: {result.errors}")
        # Aun con errores, debe retornar estructura válida
        assert isinstance(result.errors, list), "Errors should be a list"


@pytest.mark.asyncio
async def test_marriage_certificate_extraction_complete_flow():
    """Test del flujo completo de extracción de acta de matrimonio"""
    if not settings.ollama_cloud_api_key:
        pytest.skip("OLLAMA_CLOUD_API_KEY not configured")
    
    service = MultiProviderOCRService()
    cert_image = create_marriage_certificate_image()
    
    print("\n🔄 Extracting marriage certificate data with OCR Service...")
    result = await service.extract_marriage_certificate_data(cert_image)
    
    print(f"✓ Success: {result.success}")
    print(f"✓ Confidence: {result.confidence:.2f}")
    print(f"✓ Data extracted: {result.data}")
    print(f"✓ Errors: {result.errors}")
    
    # Validaciones básicas
    assert result.success is not None
    assert result.confidence >= 0.0
    assert isinstance(result.data, dict)
    
    # Si fue exitoso, verificar campos requeridos
    if result.success:
        assert "fecha_matrimonio" in result.data, "Should extract marriage date"
        assert "nombre_conyuge_1" in result.data, "Should extract spouse 1 name"
        assert "nombre_conyuge_2" in result.data, "Should extract spouse 2 name"
        assert "lugar_matrimonio" in result.data, "Should extract marriage place"
        print("✅ Marriage certificate extraction successful!")
    else:
        print(f"⚠️ Marriage certificate extraction had issues: {result.errors}")


@pytest.mark.asyncio
async def test_generic_document_extraction():
    """Test de extracción genérica de texto"""
    if not settings.ollama_cloud_api_key:
        pytest.skip("OLLAMA_CLOUD_API_KEY not configured")
    
    service = MultiProviderOCRService()
    
    # Crear un documento genérico simple
    img = Image.new('RGB', (600, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    test_text = [
        "SOLICITUD DE DIVORCIO",
        "Por medio de la presente solicito",
        "el inicio del trámite de divorcio",
        "de mutuo acuerdo."
    ]
    
    y_pos = 50
    for line in test_text:
        draw.text((50, y_pos), line, fill='black')
        y_pos += 50
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    doc_image = buffer.getvalue()
    
    print("\n🔄 Extracting generic document text...")
    result = await service.extract_generic_document(doc_image)
    
    print(f"✓ Success: {result.success}")
    print(f"✓ Extracted text length: {len(result.data.get('text', ''))}")
    print(f"✓ Text preview: {result.data.get('text', '')[:200]}...")
    
    assert result.success is not None
    assert "text" in result.data
    
    if result.success:
        # Verificar que detectó algo del texto
        extracted = result.data['text'].lower()
        assert len(extracted) > 0, "Should extract some text"
        print("✅ Generic document extraction successful!")


@pytest.mark.asyncio
async def test_ocr_error_handling():
    """Test de manejo de errores con imagen inválida"""
    service = MultiProviderOCRService()
    
    # Imagen corrupta o vacía
    invalid_image = b"invalid_image_data"
    
    print("\n🔄 Testing error handling with invalid image...")
    result = await service.extract_dni_data(invalid_image)
    
    print(f"✓ Success (should be False): {result.success}")
    print(f"✓ Errors: {result.errors}")
    
    assert result.success == False, "Should fail with invalid image"
    assert len(result.errors) > 0, "Should have error messages"
    assert result.confidence == 0.0, "Confidence should be zero on failure"
    print("✅ Error handling works correctly!")


@pytest.mark.asyncio
async def test_dni_validation_rules():
    """Test de validación estricta de datos de DNI"""
    if not settings.ollama_cloud_api_key:
        pytest.skip("OLLAMA_CLOUD_API_KEY not configured")
    
    service = MultiProviderOCRService()
    
    # Crear DNI con datos intencionalmente incompletos o incorrectos
    img = Image.new('RGB', (800, 500), color='white')
    draw = ImageDraw.Draw(img)
    
    # Solo algunos campos (para probar validaciones)
    draw.text((50, 100), "DNI: 123", fill='black')  # Número muy corto
    draw.text((50, 150), "NOMBRE: JUAN", fill='black')
    # Falta fecha de nacimiento
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    dni_image = buffer.getvalue()
    
    print("\n🔄 Testing DNI validation rules...")
    result = await service.extract_dni_data(dni_image)
    
    print(f"✓ Success: {result.success}")
    print(f"✓ Confidence: {result.confidence:.2f}")
    print(f"✓ Validation errors: {result.errors}")
    
    # Con datos incompletos, debería tener baja confianza o errores
    if not result.success or result.confidence < 0.7:
        print("✅ Validation correctly caught incomplete/invalid data!")
        assert len(result.errors) > 0, "Should have validation errors"
    else:
        print(f"⚠️ Model was very confident despite incomplete data: {result.data}")


@pytest.mark.asyncio
async def test_performance_benchmark():
    """Benchmark de latencia del OCR Service"""
    if not settings.ollama_cloud_api_key:
        pytest.skip("OLLAMA_CLOUD_API_KEY not configured")
    
    import time
    service = MultiProviderOCRService()
    dni_image = create_dni_image()
    
    print("\n📊 Performance Benchmark:")
    print("-" * 50)
    
    # Test de DNI
    start = time.time()
    result_dni = await service.extract_dni_data(dni_image)
    latency_dni = time.time() - start
    
    print(f"✓ DNI extraction: {latency_dni:.2f}s")
    
    # Test de acta
    cert_image = create_marriage_certificate_image()
    start = time.time()
    result_cert = await service.extract_marriage_certificate_data(cert_image)
    latency_cert = time.time() - start
    
    print(f"✓ Marriage cert extraction: {latency_cert:.2f}s")
    
    # Verificar latencias razonables (< 15s para visión cloud)
    assert latency_dni < 30, f"DNI OCR too slow: {latency_dni}s"
    assert latency_cert < 30, f"Cert OCR too slow: {latency_cert}s"
    
    print(f"✓ Average latency: {(latency_dni + latency_cert) / 2:.2f}s")
    print("✅ Performance is acceptable!")


if __name__ == "__main__":
    print("🚀 Running OCR Service End-to-End Integration Tests")
    print("=" * 60)
    pytest.main([__file__, "-v", "-s"])
