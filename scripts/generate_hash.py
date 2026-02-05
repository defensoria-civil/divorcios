"""
Genera un hash de contraseña válido para el usuario
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))

from passlib.context import CryptContext

# Mismo contexto que usa la aplicación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generar hash para "password123"
password = "password123"
hashed = pwd_context.hash(password)

print(f"Password: {password}")
print(f"Hash: {hashed}")
print(f"\nSQL para actualizar:")
print(f"UPDATE users SET hashed_password = '{hashed}' WHERE username = 'semper';")
