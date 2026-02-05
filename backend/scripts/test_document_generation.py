#!/usr/bin/env python3
"""
Script de prueba para generación de documentos legales de divorcio.
Genera PDFs de ejemplo para casos bilaterales y unilaterales.
"""
import sys
from pathlib import Path
from datetime import date

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.document.pdf_service_impl import TemplatePDFService

def test_divorcio_bilateral():
    """Prueba de generación de divorcio bilateral."""
    print("\n📄 Generando documento: Divorcio Bilateral")
    print("=" * 60)
    
    case_data = {
        "type": "bilateral",
        # Persona 1
        "apellido": "GARCÍA",
        "nombres": "MARÍA LAURA",
        "dni": "28.345.678",
        "nacionalidad": "argentina",
        "ocupacion": "empleada administrativa",
        "domicilio": "Calle San Martín 1234, San Rafael, Mendoza",
        "phone": "+54 260 4123456",
        "email": "maria.garcia@example.com",
        "fecha_nacimiento": date(1982, 5, 15),
        
        # Persona 2 (cónyuge)
        "apellido_conyuge": "RODRÍGUEZ",
        "nombres_conyuge": "CARLOS ALBERTO",
        "dni_conyuge": "27.654.321",
        "nacionalidad_conyuge": "argentino",
        "ocupacion_conyuge": "comerciante",
        "domicilio_conyuge": "Av. Balloffet 567, San Rafael, Mendoza",
        "phone_conyuge": "+54 260 4987654",
        "email_conyuge": "carlos.rodriguez@example.com",
        "fecha_nacimiento_conyuge": date(1980, 8, 22),
        
        # Acta de matrimonio
        "acta_numero": "123",
        "acta_libro": "XV",
        "acta_anio": "2005",
        "acta_foja": "45",
        "acta_oficina": "Registro Civil San Rafael",
        
        # Datos del matrimonio
        "fecha_matrimonio": "20 de marzo de 2005",
        "lugar_matrimonio": "San Rafael, Mendoza",
        "fecha_separacion": "15 de enero de 2024",
        "ultimo_domicilio_conyugal": "Calle San Martín 1234, San Rafael, Mendoza",
        
        # Bienes e hijos
        "tiene_bienes": False,
        "bienes_muebles_text": "Los bienes muebles fueron repartidos de común acuerdo al momento de la separación.",
        "tiene_hijos": True,
        "info_hijos": "Del matrimonio nacieron dos hijos: LUCAS GARCÍA RODRÍGUEZ (15 años, DNI 45.123.456) y SOFÍA GARCÍA RODRÍGUEZ (12 años, DNI 46.789.012), ambos mayores de 13 años. Se ha acordado la tenencia compartida y ambos progenitores ejercen la responsabilidad parental.",
        
        # Defensoría
        "letrada_nombre": "MARIA JORGELINA BAYÓN",
        "defensoria_nombre": "Cuarta Defensoría de Pobres y Ausentes de la Segunda Circunscripción Judicial de Mendoza",
        "office_address": "E. Civit N° 257, San Rafael, Mendoza"
    }
    
    service = TemplatePDFService()
    pdf_bytes = service.generate_divorce_petition_pdf(case_data)
    
    # Guardar PDF (manejar archivo bloqueado en Windows)
    output_path = Path(__file__).parent / "output_divorcio_bilateral.pdf"
    try:
        output_path.write_bytes(pdf_bytes)
    except PermissionError:
        # Si el archivo está abierto, intentar con nombre alternativo
        import time
        timestamp = int(time.time())
        output_path = Path(__file__).parent / f"output_divorcio_bilateral_{timestamp}.pdf"
        output_path.write_bytes(pdf_bytes)
        print(f"⚠️  Archivo original bloqueado, guardado como: {output_path.name}")
    
    print(f"✅ Documento generado: {output_path}")
    print(f"   Tamaño: {len(pdf_bytes):,} bytes")
    print(f"   Tipo: Divorcio Bilateral")
    print(f"   Partes: {case_data['nombres']} {case_data['apellido']} y {case_data['nombres_conyuge']} {case_data['apellido_conyuge']}")
    return True

def test_divorcio_unilateral():
    """Prueba de generación de divorcio unilateral."""
    print("\n📄 Generando documento: Divorcio Unilateral")
    print("=" * 60)
    
    case_data = {
        "type": "unilateral",
        # Persona 1 (quien solicita)
        "apellido": "FERNÁNDEZ",
        "nombres": "ANA BEATRIZ",
        "dni": "30.456.789",
        "nacionalidad": "argentina",
        "ocupacion": "docente",
        "domicilio": "Calle Mitre 890, San Rafael, Mendoza",
        "phone": "+54 260 4555666",
        "email": "ana.fernandez@example.com",
        "fecha_nacimiento": date(1985, 11, 3),
        
        # Persona 2 (cónyuge demandado)
        "apellido_conyuge": "MARTÍNEZ",
        "nombres_conyuge": "JORGE LUIS",
        "dni_conyuge": "29.987.654",
        "domicilio_conyuge": "Calle Belgrano 432, San Rafael, Mendoza",
        
        # Acta de matrimonio
        "acta_numero": "456",
        "acta_libro": "XX",
        "acta_anio": "2010",
        "acta_foja": "78",
        "acta_oficina": "Registro Civil San Rafael",
        
        # Datos del matrimonio
        "fecha_matrimonio": "12 de diciembre de 2010",
        "lugar_matrimonio": "San Rafael, Mendoza",
        "fecha_separacion": "30 de junio de 2023",
        "ultimo_domicilio_conyugal": "Calle Mitre 890, San Rafael, Mendoza",
        
        # Bienes e hijos
        "tiene_bienes": True,
        "info_bienes": "La vivienda que fuera asiento del hogar conyugal es un bien propio de la Sra. FERNÁNDEZ, adquirido antes del matrimonio, por lo que no corresponde liquidación.",
        "bienes_muebles_text": "Los bienes muebles fueron repartidos al momento de la separación según inventario que se acompaña.",
        "tiene_hijos": False,
        
        # Defensoría
        "letrada_nombre": "MARIA JORGELINA BAYÓN",
        "defensoria_nombre": "Cuarta Defensoría de Pobres y Ausentes de la Segunda Circunscripción Judicial de Mendoza",
        "office_address": "E. Civit N° 257, San Rafael, Mendoza"
    }
    
    service = TemplatePDFService()
    pdf_bytes = service.generate_divorce_petition_pdf(case_data)
    
    # Guardar PDF (manejar archivo bloqueado en Windows)
    output_path = Path(__file__).parent / "output_divorcio_unilateral.pdf"
    try:
        output_path.write_bytes(pdf_bytes)
    except PermissionError:
        import time
        timestamp = int(time.time())
        output_path = Path(__file__).parent / f"output_divorcio_unilateral_{timestamp}.pdf"
        output_path.write_bytes(pdf_bytes)
        print(f"⚠️  Archivo original bloqueado, guardado como: {output_path.name}")
    
    print(f"✅ Documento generado: {output_path}")
    print(f"   Tamaño: {len(pdf_bytes):,} bytes")
    print(f"   Tipo: Divorcio Unilateral")
    print(f"   Solicitante: {case_data['nombres']} {case_data['apellido']}")
    print(f"   Demandado: {case_data['nombres_conyuge']} {case_data['apellido_conyuge']}")
    return True

def test_caso_minimalista():
    """Prueba con datos mínimos requeridos."""
    print("\n📄 Generando documento: Caso Minimalista")
    print("=" * 60)
    
    case_data = {
        "type": "bilateral",
        "apellido": "PÉREZ",
        "nombres": "JUAN",
        "dni": "25.111.222",
        "domicilio": "Calle Principal 100, San Rafael",
        
        "apellido_conyuge": "LÓPEZ",
        "nombres_conyuge": "MARÍA",
        "dni_conyuge": "26.333.444",
        
        "acta_numero": "789",
        "acta_libro": "XXV",
        "acta_anio": "2015",
        "acta_foja": "12",
        "acta_oficina": "Registro Civil",
        
        "fecha_matrimonio": "10/05/2015",
        "lugar_matrimonio": "San Rafael",
        "fecha_separacion": "01/01/2024",
        
        "tiene_bienes": False,
        "tiene_hijos": False,
    }
    
    service = TemplatePDFService()
    pdf_bytes = service.generate_divorce_petition_pdf(case_data)
    
    # Guardar PDF (manejar archivo bloqueado en Windows)
    output_path = Path(__file__).parent / "output_divorcio_minimal.pdf"
    try:
        output_path.write_bytes(pdf_bytes)
    except PermissionError:
        import time
        timestamp = int(time.time())
        output_path = Path(__file__).parent / f"output_divorcio_minimal_{timestamp}.pdf"
        output_path.write_bytes(pdf_bytes)
        print(f"⚠️  Archivo original bloqueado, guardado como: {output_path.name}")
    
    print(f"✅ Documento generado: {output_path}")
    print(f"   Tamaño: {len(pdf_bytes):,} bytes")
    print(f"   Nota: Documento con datos mínimos requeridos")
    return True

def main():
    print("\n" + "=" * 60)
    print("🧪 PRUEBAS DE GENERACIÓN DE DOCUMENTOS LEGALES")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Divorcio Bilateral", test_divorcio_bilateral()))
    except Exception as e:
        print(f"❌ Error en Divorcio Bilateral: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Divorcio Bilateral", False))
    
    try:
        results.append(("Divorcio Unilateral", test_divorcio_unilateral()))
    except Exception as e:
        print(f"❌ Error en Divorcio Unilateral: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Divorcio Unilateral", False))
    
    try:
        results.append(("Caso Minimalista", test_caso_minimalista()))
    except Exception as e:
        print(f"❌ Error en Caso Minimalista: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Caso Minimalista", False))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    for nombre, resultado in results:
        icono = "✅" if resultado else "❌"
        print(f"{icono} {nombre}")
    
    total = len(results)
    exitosos = sum(1 for _, r in results if r)
    print(f"\nTotal: {exitosos}/{total} pruebas exitosas")
    
    if exitosos == total:
        print("\n🎉 Todas las pruebas pasaron correctamente!")
        return 0
    else:
        print(f"\n⚠️  {total - exitosos} prueba(s) fallaron")
        return 1

if __name__ == "__main__":
    sys.exit(main())
