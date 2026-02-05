"""
Script para crear un usuario de prueba en la base de datos.
Uso: python create_test_user.py
"""
import sys
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.persistence.db import SessionLocal, engine, Base
from infrastructure.persistence.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_user():
    """Crea un usuario de prueba para el sistema"""
    # Crear tablas si no existen
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Verificar si el usuario ya existe
        existing_user = db.query(User).filter(User.email == "semper@gmail.com").first()
        if existing_user:
            print("❌ El usuario semper@gmail.com ya existe")
            print(f"   Username: {existing_user.username}")
            print(f"   Nombre: {existing_user.full_name}")
            print(f"   Rol: {existing_user.role}")
            return
        
        # Crear el usuario de prueba
        hashed_password = pwd_context.hash("password123")
        test_user = User(
            username="semper",
            email="semper@gmail.com",
            hashed_password=hashed_password,
            full_name="Sebastian Pereyra",
            role="admin",
            is_active=True
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print("✅ Usuario de prueba creado exitosamente!")
        print(f"   Email: {test_user.email}")
        print(f"   Username: {test_user.username}")
        print(f"   Password: password123")
        print(f"   Nombre: {test_user.full_name}")
        print(f"   Rol: {test_user.role}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear usuario: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
