"""
Script para crear un usuario admin directamente en la base de datos.
"""
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configurar DATABASE_URL antes de importar
os.environ['DATABASE_URL'] = 'postgresql+psycopg2://postgres:postgres@localhost:5433/def_civil'

from infrastructure.persistence.db import SessionLocal
from infrastructure.persistence.repositories import UserRepository

def create_admin_user():
    """Crea un usuario administrador"""
    db = SessionLocal()
    try:
        users_repo = UserRepository(db)
        
        # Verificar si ya existe
        existing = users_repo.get_by_username("semper")
        if existing:
            print("⚠️  El usuario 'semper' ya existe")
            print(f"   ID: {existing.id}")
            print(f"   Email: {existing.email}")
            print(f"   Rol: {existing.role}")
            print(f"   Activo: {existing.is_active}")
            return
        
        # Crear usuario admin
        user = users_repo.create_user(
            username="semper",
            email="semper@gmail.com",
            password="password123",
            full_name="Sebastian Pereyra",
            role="admin"
        )
        
        print("✅ Usuario admin creado exitosamente!")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Nombre: {user.full_name}")
        print(f"   Rol: {user.role}")
        print(f"   ID: {user.id}")
        
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
