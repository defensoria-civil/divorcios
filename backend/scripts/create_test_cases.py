"""
Script para crear casos de prueba en la base de datos.
Uso: python create_test_cases.py
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.models import Case, Message

def create_test_cases():
    """Crea casos de prueba para testing del dashboard"""
    db = SessionLocal()
    
    try:
        # Verificar si ya hay casos
        existing_count = db.query(Case).count()
        if existing_count > 0:
            print(f"Ya existen {existing_count} casos en la base de datos.")
            response = input("¿Deseas agregar más casos de prueba? (s/n): ")
            if response.lower() != 's':
                print("Operación cancelada.")
                return
        
        # Datos de prueba
        test_cases = [
            {
                "phone": "+5492604123456",
                "status": "new",
                "type": "unilateral",
                "nombre": "Juan Pérez",
                "dni": "30123456",
                "phase": "inicio"
            },
            {
                "phone": "+5492604234567",
                "status": "new",
                "type": "conjunta",
                "nombre": "María González",
                "dni": "28456789",
                "phase": "datos_personales"
            },
            {
                "phone": "+5492604345678",
                "status": "new",
                "type": "unilateral",
                "nombre": "Carlos López",
                "dni": "32789012",
                "phase": "documentacion"
            },
            {
                "phone": "+5492604456789",
                "status": "completed",
                "type": "conjunta",
                "nombre": "Ana Martínez",
                "dni": "29345678",
                "phase": "completado",
                "fecha_matrimonio": datetime(2010, 5, 15).date()
            },
            {
                "phone": "+5492604567890",
                "status": "waiting_documents",
                "type": "unilateral",
                "nombre": "Roberto Fernández",
                "dni": "31234567",
                "phase": "documentacion"
            },
        ]
        
        created_count = 0
        for case_data in test_cases:
            # Crear caso
            case = Case(**case_data)
            
            # Variar la fecha de creación para el timeline
            days_ago = random.randint(0, 30)
            case.created_at = datetime.utcnow() - timedelta(days=days_ago)
            case.updated_at = case.created_at
            
            db.add(case)
            db.flush()  # Para obtener el ID
            
            # Agregar algunos mensajes de ejemplo
            messages = [
                Message(
                    case_id=case.id,
                    role="user",
                    content=f"Hola, necesito ayuda con mi divorcio",
                    created_at=case.created_at
                ),
                Message(
                    case_id=case.id,
                    role="assistant",
                    content=f"Hola {case.nombre}, estoy aquí para ayudarte. ¿Tu divorcio es de mutuo acuerdo o unilateral?",
                    created_at=case.created_at + timedelta(seconds=2)
                ),
            ]
            
            for msg in messages:
                db.add(msg)
            
            created_count += 1
            print(f"✅ Caso creado: {case.nombre} ({case.phone}) - Estado: {case.status}")
        
        db.commit()
        print(f"\n🎉 Se crearon {created_count} casos de prueba exitosamente!")
        print(f"📊 Total de casos en la base de datos: {db.query(Case).count()}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear casos: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_cases()
