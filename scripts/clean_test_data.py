#!/usr/bin/env python3
"""
Script para limpiar datos de prueba de la base de datos.
Preserva: usuarios, base de conocimiento (semantic_knowledge)
Elimina: cases, messages, memories
"""

import subprocess
import sys

# Configuración
DB_CONTAINER = "divorcios-db-1"
DB_NAME = "def_civil"
DB_USER = "postgres"

# Colores para terminal
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

def print_colored(text, color):
    """Imprime texto con color en la terminal"""
    print(f"{color}{text}{Colors.RESET}")

def run_psql_command(sql_command):
    """Ejecuta un comando SQL en el contenedor PostgreSQL"""
    cmd = [
        "docker", "exec", "-i", DB_CONTAINER,
        "psql", "-U", DB_USER, "-d", DB_NAME, "-c", sql_command
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def get_counts():
    """Obtiene el conteo de registros"""
    query = """
    SELECT 
        (SELECT COUNT(*) FROM cases) as cases,
        (SELECT COUNT(*) FROM messages) as messages,
        (SELECT COUNT(*) FROM memories WHERE kind IN ('immediate', 'session', 'episodic')) as memories,
        (SELECT COUNT(*) FROM semantic_knowledge) as knowledge_base;
    """
    return run_psql_command(query)

def clean_database():
    """Limpia los datos de prueba de la base de datos"""
    print_colored("🧹 Limpiando datos de prueba...", Colors.CYAN)
    print()
    
    # Confirmar con el usuario
    response = input("⚠️  Esto eliminará TODOS los casos, mensajes y memorias. ¿Continuar? (s/N): ")
    if response.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
        print_colored("❌ Operación cancelada", Colors.RED)
        sys.exit(1)
    
    print()
    print_colored("📊 Conteo de registros antes de limpiar:", Colors.YELLOW)
    print(get_counts())
    
    print_colored("🗑️  Eliminando datos de prueba...", Colors.YELLOW)
    
    # Eliminar en orden (respetando foreign keys)
    delete_script = """
        -- Eliminar mensajes
        DELETE FROM messages;
        
        -- Eliminar memorias de casos (preservar semantic_knowledge)
        DELETE FROM memories WHERE kind IN ('immediate', 'session', 'episodic');
        
        -- Eliminar casos
        DELETE FROM cases;
        
        -- Resetear secuencias
        ALTER SEQUENCE cases_id_seq RESTART WITH 1;
        ALTER SEQUENCE messages_id_seq RESTART WITH 1;
        ALTER SEQUENCE memories_id_seq RESTART WITH 1;
    """
    
    # Ejecutar eliminación
    run_psql_command(delete_script)
    
    print()
    print_colored("✅ Limpieza completada", Colors.GREEN)
    print()
    print_colored("📊 Conteo de registros después de limpiar:", Colors.YELLOW)
    print(get_counts())
    
    print()
    print_colored("🎉 Base de datos lista para nuevas pruebas", Colors.GREEN)
    print("   ✓ Casos eliminados")
    print("   ✓ Mensajes eliminados")
    print("   ✓ Memorias de casos eliminadas")
    print("   ✓ Base de conocimiento preservada")
    print("   ✓ Usuarios preservados")

if __name__ == "__main__":
    try:
        clean_database()
    except KeyboardInterrupt:
        print()
        print_colored("❌ Operación cancelada por el usuario", Colors.RED)
        sys.exit(1)
    except Exception as e:
        print_colored(f"❌ Error: {e}", Colors.RED)
        sys.exit(1)
