"""
Script para verificar el estado de la base de datos y crear las tablas si no existen.
"""
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infrastructure.persistence.db import init_db, engine
from sqlalchemy import text

def check_and_init_db():
    print("→ Verificando conexión a la base de datos...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Conexión exitosa a la base de datos")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False
    
    print("\n→ Inicializando tablas...")
    try:
        init_db()
        print("✅ Tablas creadas/verificadas exitosamente")
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n→ Verificando tablas existentes...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            if tables:
                print("✅ Tablas encontradas:")
                for table in tables:
                    print(f"   - {table}")
            else:
                print("⚠️  No se encontraron tablas")
    except Exception as e:
        print(f"❌ Error al listar tablas: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = check_and_init_db()
    sys.exit(0 if success else 1)
