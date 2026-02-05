"""
Script de prueba para verificar los nuevos endpoints de generación de PDF
Ejecutar desde la raíz del backend: python scripts/test_pdf_endpoints.py
"""

import requests
import json
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:8000"
CASE_ID = 1  # Cambiar por un ID de caso real

# Token de autenticación (obtener del login)
# Ejecutar primero: curl -X POST http://localhost:8000/api/auth/login -d '{"username":"admin","password":"admin"}'
TOKEN = "YOUR_JWT_TOKEN_HERE"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_validate_endpoint():
    """Prueba el endpoint de validación"""
    print("\n" + "="*60)
    print("🔍 TEST 1: Validación de Datos")
    print("="*60)
    
    url = f"{BASE_URL}/api/cases/{CASE_ID}/validate"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Completitud: {data['completion_percentage']}%")
        print(f"✅ Campos completos: {len(data['complete_fields'])}")
        print(f"❌ Campos faltantes: {len(data['missing_fields'])}")
        print(f"🔵 Campos opcionales: {len(data['optional_fields'])}")
        
        if data['missing_fields']:
            print("\n⚠️  Campos que faltan:")
            for field in data['missing_fields']:
                print(f"   - {field['label']} ({field['field']})")
        
        return data
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   {response.text}")
        return None

def test_update_endpoint():
    """Prueba el endpoint de actualización"""
    print("\n" + "="*60)
    print("📝 TEST 2: Actualización de Campos")
    print("="*60)
    
    # Datos de prueba para actualizar
    updates = {
        "acta_numero": "123456",
        "acta_libro": "5",
        "acta_anio": "2015",
        "acta_foja": "78",
        "acta_oficina": "Registro Civil San Rafael"
    }
    
    url = f"{BASE_URL}/api/cases/{CASE_ID}"
    response = requests.patch(url, headers=headers, json=updates)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Mensaje: {data['message']}")
        print(f"📝 Campos actualizados: {', '.join(data['updated_fields'])}")
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   {response.text}")
        return False

def test_pdf_generation():
    """Prueba la generación del PDF"""
    print("\n" + "="*60)
    print("📄 TEST 3: Generación de PDF")
    print("="*60)
    
    url = f"{BASE_URL}/api/cases/{CASE_ID}/petition.pdf"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Guardar PDF
        output_path = Path(__file__).parent / f"test_case_{CASE_ID}.pdf"
        output_path.write_bytes(response.content)
        
        size_kb = len(response.content) / 1024
        print(f"✅ Status: {response.status_code}")
        print(f"📄 PDF generado exitosamente")
        print(f"💾 Guardado en: {output_path}")
        print(f"📏 Tamaño: {size_kb:.2f} KB")
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   {response.text}")
        return False

def run_all_tests():
    """Ejecuta todos los tests en secuencia"""
    print("\n" + "="*60)
    print("🚀 INICIANDO PRUEBAS DE ENDPOINTS DE PDF")
    print("="*60)
    
    if TOKEN == "YOUR_JWT_TOKEN_HERE":
        print("\n❌ ERROR: Debes configurar el TOKEN primero")
        print("   1. Hacer login: POST /api/auth/login")
        print("   2. Copiar el token JWT")
        print("   3. Actualizar la variable TOKEN en este script")
        return
    
    # Test 1: Validar datos
    validation_data = test_validate_endpoint()
    
    if not validation_data:
        print("\n❌ No se pudo validar el caso. Abortando tests.")
        return
    
    # Test 2: Actualizar campos (solo si hay campos faltantes)
    if validation_data['missing_fields']:
        print("\n⏳ Esperando 2 segundos antes del siguiente test...")
        import time
        time.sleep(2)
        
        test_update_endpoint()
        
        # Re-validar después de actualizar
        print("\n🔄 Re-validando después de actualizar...")
        validation_data = test_validate_endpoint()
    
    # Test 3: Generar PDF
    if validation_data and validation_data['completion_percentage'] >= 80:
        print("\n⏳ Esperando 2 segundos antes del siguiente test...")
        import time
        time.sleep(2)
        
        test_pdf_generation()
    else:
        print("\n⚠️  Completitud menor al 80%. Generando PDF de todas formas...")
        test_pdf_generation()
    
    print("\n" + "="*60)
    print("✅ PRUEBAS COMPLETADAS")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
