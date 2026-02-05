#!/usr/bin/env python3
"""
Script de validación de documentos generados.
Verifica que los PDFs contengan los elementos legales requeridos.
"""
import sys
from pathlib import Path
from datetime import date

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.document.pdf_service_impl import TemplatePDFService
from jinja2 import Environment, FileSystemLoader

def validate_template_rendering():
    """Valida que las plantillas rendericen correctamente sin generar PDF."""
    print("\n🔍 Validando renderizado de plantillas")
    print("=" * 60)
    
    base = Path(__file__).parent.parent
    templates_dir = base / "templates" / "legal"
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    
    # Caso de prueba
    case_data = {
        "type": "bilateral",
        "apellido": "GARCÍA",
        "nombres": "MARÍA",
        "dni": "12.345.678",
        "domicilio": "Calle 123",
        "apellido_conyuge": "LÓPEZ",
        "nombres_conyuge": "JUAN",
        "dni_conyuge": "87.654.321",
        "acta_numero": "123",
        "acta_libro": "X",
        "acta_anio": "2020",
        "acta_foja": "45",
        "acta_oficina": "RC San Rafael",
        "fecha_matrimonio": "01/01/2020",
        "lugar_matrimonio": "San Rafael",
        "fecha_separacion": "01/01/2024",
    }
    
    service = TemplatePDFService()
    context = service._build_context(case_data)
    
    # Test bilateral
    template_bilateral = env.get_template("divorcio_bilateral.j2")
    rendered_bilateral = template_bilateral.render(**context)
    
    # Validaciones de contenido
    checks = []
    
    # Check 1: Contiene nombres de las partes
    check1 = "GARCÍA" in rendered_bilateral and "LÓPEZ" in rendered_bilateral
    checks.append(("Nombres de partes presentes", check1))
    
    # Check 2: Contiene DNIs
    check2 = "12.345.678" in rendered_bilateral and "87.654.321" in rendered_bilateral
    checks.append(("DNIs presentes", check2))
    
    # Check 3: Contiene secciones obligatorias
    secciones = [
        "I. DATOS PERSONALES",
        "II. DOMICILIO LEGAL",
        "III. BENEFICIO DE LITIGAR SIN GASTOS",
        "IV. COMPETENCIA",
        "V. OBJETO",
        "VI. HECHOS",
        "VII. PROPUESTA REGULADORA",
        "VIII. PRUEBA",
        "IX. DERECHO",
        "X. PETITORIO"
    ]
    check3 = all(sec in rendered_bilateral for sec in secciones)
    checks.append(("Todas las secciones presentes", check3))
    
    # Check 4: Contiene datos del acta
    check4 = "123" in rendered_bilateral and "Libro Registro" in rendered_bilateral
    checks.append(("Datos del acta presentes", check4))
    
    # Check 5: Contiene referencias legales
    check5 = "C.C.C.N" in rendered_bilateral and "Ley 9120" in rendered_bilateral
    checks.append(("Referencias legales presentes", check5))
    
    # Test unilateral - el encabezado se agrega en el código, no en el template
    case_data["type"] = "unilateral"
    template_unilateral = env.get_template("divorcio_unilateral.j2")
    rendered_unilateral = template_unilateral.render(**context)
    
    # Verificar que el template unilateral tenga el contenido correcto (SEÑORA JUEZA presente)
    check6 = "SEÑORA JUEZA" in rendered_unilateral
    checks.append(("Template unilateral correcto", check6))
    
    # Reporte
    print("\nResultados de validación:")
    for descripcion, resultado in checks:
        icono = "✅" if resultado else "❌"
        print(f"  {icono} {descripcion}")
    
    total = len(checks)
    exitosos = sum(1 for _, r in checks if r)
    
    print(f"\n📊 {exitosos}/{total} validaciones exitosas")
    
    if exitosos == total:
        print("✅ Todas las validaciones pasaron")
        return True
    else:
        print(f"❌ {total - exitosos} validaciones fallaron")
        return False

def validate_field_mapping():
    """Valida que todos los campos del modelo se mapeen correctamente."""
    print("\n🗺️  Validando mapeo de campos")
    print("=" * 60)
    
    service = TemplatePDFService()
    
    # Caso completo con todos los campos
    case_data = {
        "type": "bilateral",
        "apellido": "GARCÍA",
        "nombres": "MARÍA LAURA",
        "dni": "28.345.678",
        "nacionalidad": "argentina",
        "ocupacion": "empleada",
        "domicilio": "Calle 123",
        "phone": "+54 260 123456",
        "email": "test@example.com",
        "fecha_nacimiento": date(1982, 5, 15),
        
        "apellido_conyuge": "LÓPEZ",
        "nombres_conyuge": "JUAN CARLOS",
        "dni_conyuge": "27.654.321",
        "nacionalidad_conyuge": "argentino",
        "ocupacion_conyuge": "comerciante",
        "domicilio_conyuge": "Calle 456",
        "phone_conyuge": "+54 260 654321",
        "email_conyuge": "test2@example.com",
        "fecha_nacimiento_conyuge": date(1980, 8, 22),
        
        "acta_numero": "123",
        "acta_libro": "XV",
        "acta_anio": "2005",
        "acta_foja": "45",
        "acta_oficina": "RC San Rafael",
        
        "fecha_matrimonio": "20 de marzo de 2005",
        "lugar_matrimonio": "San Rafael",
        "fecha_separacion": "15 de enero de 2024",
        "ultimo_domicilio_conyugal": "Calle 123",
        
        "tiene_bienes": True,
        "info_bienes": "Información de bienes",
        "bienes_muebles_text": "Bienes muebles",
        "tiene_hijos": True,
        "info_hijos": "Información de hijos",
    }
    
    context = service._build_context(case_data)
    
    # Verificaciones
    checks = []
    
    # Persona 1
    checks.append(("persona1.apellido", context["persona1"]["apellido"] == "GARCÍA"))
    checks.append(("persona1.nombres", context["persona1"]["nombres"] == "MARÍA LAURA"))
    checks.append(("persona1.dni", context["persona1"]["dni"] == "28.345.678"))
    checks.append(("persona1.edad calculada", context["persona1"]["edad"] is not None))
    
    # Persona 2
    checks.append(("persona2.apellido", context["persona2"]["apellido"] == "LÓPEZ"))
    checks.append(("persona2.nombres", context["persona2"]["nombres"] == "JUAN CARLOS"))
    
    # Acta
    checks.append(("acta.numero", context["acta"]["numero"] == "123"))
    checks.append(("acta.libro", context["acta"]["libro"] == "XV"))
    
    # Otros campos
    checks.append(("fecha_matrimonio", context["fecha_matrimonio"] is not None))
    checks.append(("tiene_bienes", context["tiene_bienes"] == True))
    checks.append(("tiene_hijos", context["tiene_hijos"] == True))
    
    # Reporte
    print("\nResultados de mapeo:")
    for campo, resultado in checks:
        icono = "✅" if resultado else "❌"
        print(f"  {icono} {campo}")
    
    total = len(checks)
    exitosos = sum(1 for _, r in checks if r)
    
    print(f"\n📊 {exitosos}/{total} campos mapeados correctamente")
    
    if exitosos == total:
        print("✅ Todos los campos se mapean correctamente")
        return True
    else:
        print(f"❌ {total - exitosos} campos tienen problemas")
        return False

def validate_edge_cases():
    """Valida casos límite y datos opcionales."""
    print("\n⚠️  Validando casos límite")
    print("=" * 60)
    
    service = TemplatePDFService()
    checks = []
    
    # Test 1: Datos mínimos
    try:
        minimal_data = {
            "type": "bilateral",
            "apellido": "TEST",
            "nombres": "PERSONA",
            "dni": "12345678",
            "domicilio": "Calle 1",
            "apellido_conyuge": "TEST2",
            "nombres_conyuge": "PERSONA2",
            "dni_conyuge": "87654321",
            "acta_numero": "1",
            "acta_libro": "I",
            "acta_anio": "2020",
            "acta_foja": "1",
            "acta_oficina": "RC",
            "fecha_matrimonio": "01/01/2020",
            "lugar_matrimonio": "Lugar",
            "fecha_separacion": "01/01/2024",
        }
        pdf = service.generate_divorce_petition_pdf(minimal_data)
        checks.append(("Datos mínimos", pdf is not None and len(pdf) > 0))
    except Exception as e:
        print(f"❌ Error con datos mínimos: {e}")
        checks.append(("Datos mínimos", False))
    
    # Test 2: Sin bienes ni hijos
    try:
        sin_bienes_hijos = minimal_data.copy()
        sin_bienes_hijos["tiene_bienes"] = False
        sin_bienes_hijos["tiene_hijos"] = False
        pdf = service.generate_divorce_petition_pdf(sin_bienes_hijos)
        checks.append(("Sin bienes ni hijos", pdf is not None and len(pdf) > 0))
    except Exception as e:
        print(f"❌ Error sin bienes/hijos: {e}")
        checks.append(("Sin bienes ni hijos", False))
    
    # Test 3: Con datos opcionales vacíos
    try:
        datos_vacios = minimal_data.copy()
        datos_vacios.update({
            "nacionalidad": None,
            "ocupacion": None,
            "phone": None,
            "email": None,
        })
        pdf = service.generate_divorce_petition_pdf(datos_vacios)
        checks.append(("Campos opcionales vacíos", pdf is not None and len(pdf) > 0))
    except Exception as e:
        print(f"❌ Error con campos vacíos: {e}")
        checks.append(("Campos opcionales vacíos", False))
    
    # Test 4: Selección de template
    try:
        for tipo in ["bilateral", "unilateral", "conjunta"]:
            test_data = minimal_data.copy()
            test_data["type"] = tipo
            template = service._select_template(test_data)
            if tipo in ["bilateral", "conjunta"]:
                checks.append((f"Template {tipo}", template == "divorcio_bilateral.j2"))
            else:
                checks.append((f"Template {tipo}", template == "divorcio_unilateral.j2"))
    except Exception as e:
        print(f"❌ Error en selección de template: {e}")
        checks.append(("Selección de template", False))
    
    # Reporte
    print("\nResultados de casos límite:")
    for descripcion, resultado in checks:
        icono = "✅" if resultado else "❌"
        print(f"  {icono} {descripcion}")
    
    total = len(checks)
    exitosos = sum(1 for _, r in checks if r)
    
    print(f"\n📊 {exitosos}/{total} casos límite manejados correctamente")
    
    if exitosos == total:
        print("✅ Todos los casos límite se manejan correctamente")
        return True
    else:
        print(f"❌ {total - exitosos} casos tienen problemas")
        return False

def main():
    print("\n" + "=" * 60)
    print("🔬 VALIDACIÓN AVANZADA DE DOCUMENTOS LEGALES")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Renderizado de plantillas", validate_template_rendering()))
    except Exception as e:
        print(f"❌ Error en validación de renderizado: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Renderizado de plantillas", False))
    
    try:
        results.append(("Mapeo de campos", validate_field_mapping()))
    except Exception as e:
        print(f"❌ Error en validación de mapeo: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Mapeo de campos", False))
    
    try:
        results.append(("Casos límite", validate_edge_cases()))
    except Exception as e:
        print(f"❌ Error en validación de casos límite: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Casos límite", False))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VALIDACIONES")
    print("=" * 60)
    
    for nombre, resultado in results:
        icono = "✅" if resultado else "❌"
        print(f"{icono} {nombre}")
    
    total = len(results)
    exitosos = sum(1 for _, r in results if r)
    print(f"\nTotal: {exitosos}/{total} validaciones exitosas")
    
    if exitosos == total:
        print("\n🎉 ¡Todas las validaciones pasaron correctamente!")
        print("Los documentos legales se generan correctamente y cumplen")
        print("con los requisitos estructurales y de contenido.")
        return 0
    else:
        print(f"\n⚠️  {total - exitosos} validación(es) fallaron")
        return 1

if __name__ == "__main__":
    sys.exit(main())
