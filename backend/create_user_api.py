"""
Script para crear un usuario de prueba usando la API REST.
Asegúrate de que el servidor FastAPI esté corriendo en http://localhost:8000
Uso: python create_user_api.py
"""
import requests
import json

API_URL = "http://localhost:8000"

def create_test_user():
    """Crea un usuario de prueba usando el endpoint de registro"""
    
    user_data = {
        "username": "semper",
        "email": "semper@gmail.com",
        "password": "password123",
        "full_name": "Sebastian Pereyra",
        "role": "admin"
    }
    
    try:
        # Intentar crear el usuario
        response = requests.post(
            f"{API_URL}/api/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Usuario de prueba creado exitosamente!")
            print(f"   Email: {user_data['email']}")
            print(f"   Username: {user_data['username']}")
            print(f"   Password: {user_data['password']}")
            print(f"   Nombre: {user_data['full_name']}")
            print(f"   Rol: {user_data['role']}")
            print(f"\n📊 Respuesta del servidor:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Error al crear usuario (HTTP {response.status_code})")
            print(f"   Detalle: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar al servidor.")
        print("   Asegúrate de que el backend esté corriendo en http://localhost:8000")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    create_test_user()
