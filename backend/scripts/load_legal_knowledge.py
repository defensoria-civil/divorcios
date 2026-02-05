"""
Script para cargar la base de conocimiento legal sobre divorcio en Mendoza.

Carga los documentos desde los archivos Markdown y JSON preparados.
Uso: python load_legal_knowledge.py
"""
import sys
from pathlib import Path
import json
import asyncio

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.persistence.db import SessionLocal
from application.use_cases.ingest_legal_document import IngestLegalDocumentUseCase


async def load_knowledge():
    """Carga la base de conocimiento legal"""
    
    # Rutas a los archivos de conocimiento
    project_root = Path(__file__).parent.parent.parent
    md_file = project_root / "Base_Conocimiento_Divorcio_v2.md"
    json_file = project_root / "base_conocimiento_divorcio_mendoza_v2.json"
    
    db = SessionLocal()
    
    try:
        use_case = IngestLegalDocumentUseCase(db)
        
        print("📚 Cargando Base de Conocimiento Legal sobre Divorcio en Mendoza...\n")
        
        # 1. Cargar documento principal en Markdown
        if md_file.exists():
            print(f"📄 Procesando: {md_file.name}")
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result = await use_case.execute(
                title="Base de Conocimiento: Divorcio en Argentina y Mendoza",
                content=content,
                category="legislacion"
            )
            
            if result.success:
                print(f"   ✅ {result.chunks_created} chunks creados")
            else:
                print(f"   ❌ Error al procesar el documento")
        else:
            print(f"   ⚠️  Archivo no encontrado: {md_file}")
        
        # 2. Cargar documento JSON estructurado
        if json_file.exists():
            print(f"\n📄 Procesando: {json_file.name}")
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convertir JSON a texto legible
            json_content = json.dumps(data, indent=2, ensure_ascii=False)
            
            result = await use_case.execute(
                title="Base de Conocimiento JSON: Procedimientos Ley 9120",
                content=json_content,
                category="legislacion"
            )
            
            if result.success:
                print(f"   ✅ {result.chunks_created} chunks creados")
            else:
                print(f"   ❌ Error al procesar el documento")
        else:
            print(f"   ⚠️  Archivo no encontrado: {json_file}")
        
        # 3. Cargar conocimiento sobre hijos (JSON estructurado)
        hijos_json_file = project_root / "base_conocimiento_hijos_divorcio_v3.json"
        if hijos_json_file.exists():
            print(f"\n📄 Procesando: {hijos_json_file.name}")
            with open(hijos_json_file, 'r', encoding='utf-8') as f:
                data_hijos = json.load(f)
            
            # Convertir JSON a texto legible
            json_content_hijos = json.dumps(data_hijos, indent=2, ensure_ascii=False)
            
            result = await use_case.execute(
                title="Base de Conocimiento JSON: Responsabilidad Parental y Cuidado Personal",
                content=json_content_hijos,
                category="legislacion"
            )
            
            if result.success:
                print(f"   ✅ {result.chunks_created} chunks creados")
            else:
                print(f"   ❌ Error al procesar el documento")
        else:
            print(f"   ⚠️  Archivo no encontrado: {hijos_json_file}")
        
        # 4. Cargar documento Markdown sobre hijos
        hijos_md_file = project_root / "Base_Conocimiento_Hijos_v3.md"
        if hijos_md_file.exists():
            print(f"\n📄 Procesando: {hijos_md_file.name}")
            with open(hijos_md_file, 'r', encoding='utf-8') as f:
                content_hijos_md = f.read()
            
            result = await use_case.execute(
                title="Base de Conocimiento: Regulación de Hijos tras Divorcio - Terminología CCyC 2015",
                content=content_hijos_md,
                category="legislacion"
            )
            
            if result.success:
                print(f"   ✅ {result.chunks_created} chunks creados")
            else:
                print(f"   ❌ Error al procesar el documento")
        else:
            print(f"   ⚠️  Archivo no encontrado: {hijos_md_file}")
        
        # 5. Cargar conocimiento adicional específico
        print(f"\n📄 Procesando: Conocimiento Específico de Procedimientos")
        
        procedimientos_content = """
        # Procedimientos Específicos de Divorcio en Mendoza - Ley 9120
        
        ## INFORMACIÓN CRÍTICA CORREGIDA
        
        **DIVORCIO BILATERAL CON ACUERDO TOTAL:**
        - NO hay audiencia inicial
        - NO hay intento de conciliación automático
        - El juez dicta DECRETO DE DIVORCIO dentro de 10 días
        - El juez HOMOLOGA la propuesta consensuada directamente
        - Procedimiento: Presentación → Decreto → Homologación
        - Tiempo estimado: 1-2 meses
        
        **DIVORCIO BILATERAL CON DESACUERDOS PARCIALES:**
        - El juez dicta DECRETO DE DIVORCIO dentro de 10 días (primero)
        - Luego cita a AUDIENCIA para resolver efectos
        - Ambos cónyuges DEBEN asistir PERSONALMENTE
        - En audiencia se intenta solución consensuada
        - El divorcio YA está decretado, solo se discuten los efectos
        - Si hay acuerdo: Homologación inmediata
        - Si no hay acuerdo: Jurisdicción abierta
        - Tiempo estimado: 2-4 meses
        
        **DIVORCIO UNILATERAL:**
        - Demandado tiene 5 DÍAS para responder
        - Si NO responde: Decreto directo sin más trámite
        - Si ACEPTA o propuestas coinciden: Decreto y homologación
        - Si propone DIFERENTE: Audiencia (como en bilateral con desacuerdos)
        - Tiempo estimado: 1-4 meses según respuesta
        
        ## Documentos Requeridos
        
        Para cualquier tipo de divorcio:
        1. DNI de ambos cónyuges
        2. Acta de matrimonio actualizada
        3. Actas de nacimiento de hijos (si hay menores)
        4. Propuesta reguladora de efectos
        5. Patrocinio letrado (ambos deben tener abogado)
        
        ## Efectos a Regular
        
        La propuesta debe incluir:
        1. División de bienes gananciales
        2. Atribución de vivienda familiar
        3. Alimentos para hijos menores
        4. Cuidado personal de hijos (unilateral o compartido)
        5. Régimen de comunicación
        6. Compensación económica (si corresponde)
        7. Honorarios de abogados
        
        ## Competencia Territorial
        
        Es competente:
        - Juez del último domicilio conyugal efectivo, O
        - Juez del demandado (a elección del actor), O
        - Juez de cualquiera de los cónyuges (divorcio bilateral)
        
        ## Plazos Importantes
        
        - Decreto de divorcio: 10 días desde admisión
        - Respuesta en divorcio unilateral: 5 días
        - Citación a audiencia: 10 días
        - Recurso de apelación: 5 días (solo efectos, no divorcio)
        """
        
        result = await use_case.execute(
            title="Procedimientos Específicos Divorcio Mendoza",
            content=procedimientos_content,
            category="legislacion"
        )
        
        if result.success:
            print(f"   ✅ {result.chunks_created} chunks creados")
        else:
            print(f"   ❌ Error al procesar el documento")
        
        # Resumen final
        total_docs = db.query(SemanticKnowledge).count()
        print(f"\n🎉 Carga completada!")
        print(f"📊 Total de documentos en la base de conocimiento: {total_docs}")
        print(f"\n✨ El sistema ahora puede responder consultas legales basadas en este conocimiento.")
        
    except Exception as e:
        print(f"\n❌ Error durante la carga: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    from infrastructure.persistence.models import SemanticKnowledge
    asyncio.run(load_knowledge())
