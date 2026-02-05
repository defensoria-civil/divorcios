# Scripts de Limpieza de Datos de Prueba

Scripts para limpiar la base de datos después de realizar pruebas del chatbot de WhatsApp.

## ¿Qué hacen estos scripts?

### ✅ **Datos que PRESERVAN:**
- 👤 Usuarios del sistema (tabla `users`)
- 📚 Base de conocimiento legal (tabla `semantic_knowledge`)

### ❌ **Datos que ELIMINAN:**
- 📋 Casos de divorcio (tabla `cases`)
- 💬 Mensajes del chatbot (tabla `messages`)
- 🧠 Memorias de conversaciones (tabla `memories` - solo immediate/session/episodic)
- 🔄 Resetea los IDs de las secuencias a 1

## Opciones disponibles

Hay 3 versiones del script según tu sistema operativo:

### 1. **PowerShell** (Windows - RECOMENDADO)
```powershell
# Desde el directorio raíz del proyecto
.\scripts\clean_test_data.ps1
```

### 2. **Bash** (Linux/Mac/Git Bash)
```bash
# Dar permisos de ejecución (solo la primera vez)
chmod +x scripts/clean_test_data.sh

# Ejecutar
./scripts/clean_test_data.sh
```

### 3. **Python** (Cross-platform)
```bash
# Desde el directorio raíz del proyecto
python scripts/clean_test_data.py

# O con Python 3 explícitamente
python3 scripts/clean_test_data.py
```

## Ejemplo de uso

```powershell
PS C:\...\divorcios> .\scripts\clean_test_data.ps1

🧹 Limpiando datos de prueba...

⚠️  Esto eliminará TODOS los casos, mensajes y memorias. ¿Continuar? (s/N): s

📊 Conteo de registros antes de limpiar:
 cases | messages | memories | knowledge_base
-------+----------+----------+----------------
     3 |       45 |       12 |             21

🗑️  Eliminando datos de prueba...

✅ Limpieza completada

📊 Conteo de registros después de limpiar:
 cases | messages | memories | knowledge_base
-------+----------+----------+----------------
     0 |        0 |        0 |             21

🎉 Base de datos lista para nuevas pruebas
   ✓ Casos eliminados
   ✓ Mensajes eliminados
   ✓ Memorias de casos eliminadas
   ✓ Base de conocimiento preservada
   ✓ Usuarios preservados
```

## Notas importantes

⚠️ **Confirmación requerida**: Todos los scripts piden confirmación antes de ejecutar la limpieza.

⚠️ **No hay vuelta atrás**: Una vez ejecutado y confirmado, **no se puede deshacer**. Asegurate de que realmente querés eliminar todos los datos de prueba.

✅ **Seguro en producción**: El script NO elimina datos críticos (usuarios y base de conocimiento), pero igual asegurate de usarlo solo en ambientes de desarrollo/testing.

## Troubleshooting

### Error: "docker: command not found"
- Asegurate de que Docker Desktop esté corriendo
- Verificá que `docker` esté en tu PATH

### Error: "No such container: divorcios-db-1"
- Verificá que los contenedores estén corriendo: `docker ps`
- Si el contenedor tiene otro nombre, editá la variable `DB_CONTAINER` en el script

### Error de permisos en Bash
```bash
chmod +x scripts/clean_test_data.sh
```

## Workflow recomendado para testing

1. **Realizar pruebas** del chatbot vía WhatsApp
2. **Analizar resultados** y logs
3. **Ejecutar script de limpieza** cuando quieras empezar pruebas desde cero
4. **Repetir** el ciclo

Esto te permite tener un ambiente limpio para cada nueva sesión de testing sin tener que recrear toda la base de datos.
