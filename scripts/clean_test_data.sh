#!/bin/bash
# Script para limpiar datos de prueba de la base de datos
# Preserva: usuarios, base de conocimiento (semantic_knowledge)
# Elimina: cases, messages, memories

set -e

echo "🧹 Limpiando datos de prueba..."
echo ""

# Conexión a la base de datos
DB_CONTAINER="divorcios-db-1"
DB_NAME="def_civil"
DB_USER="postgres"

# Confirmar con el usuario
read -p "⚠️  Esto eliminará TODOS los casos, mensajes y memorias. ¿Continuar? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]
then
    echo "❌ Operación cancelada"
    exit 1
fi

echo ""
echo "📊 Conteo de registros antes de limpiar:"
docker exec -it $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
    SELECT 
        (SELECT COUNT(*) FROM cases) as cases,
        (SELECT COUNT(*) FROM messages) as messages,
        (SELECT COUNT(*) FROM memories WHERE kind IN ('immediate', 'session', 'episodic')) as memories,
        (SELECT COUNT(*) FROM semantic_knowledge) as knowledge_base;
"

echo ""
echo "🗑️  Eliminando datos de prueba..."

# Eliminar en orden (respetando foreign keys)
docker exec -it $DB_CONTAINER psql -U $DB_USER -d $DB_NAME <<-EOSQL
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
EOSQL

echo ""
echo "✅ Limpieza completada"
echo ""
echo "📊 Conteo de registros después de limpiar:"
docker exec -it $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
    SELECT 
        (SELECT COUNT(*) FROM cases) as cases,
        (SELECT COUNT(*) FROM messages) as messages,
        (SELECT COUNT(*) FROM memories WHERE kind IN ('immediate', 'session', 'episodic')) as memories,
        (SELECT COUNT(*) FROM semantic_knowledge) as knowledge_base;
"

echo ""
echo "🎉 Base de datos lista para nuevas pruebas"
echo "   ✓ Casos eliminados"
echo "   ✓ Mensajes eliminados"
echo "   ✓ Memorias de casos eliminadas"
echo "   ✓ Base de conocimiento preservada"
echo "   ✓ Usuarios preservados"
