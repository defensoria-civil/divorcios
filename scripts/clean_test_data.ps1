# Script para limpiar datos de prueba de la base de datos
# Preserva: usuarios, base de conocimiento (semantic_knowledge)
# Elimina: cases, messages, memories

Write-Host "🧹 Limpiando datos de prueba..." -ForegroundColor Cyan
Write-Host ""

# Conexión a la base de datos
$DB_CONTAINER = "divorcios-db-1"
$DB_NAME = "def_civil"
$DB_USER = "postgres"

# Confirmar con el usuario
$confirmation = Read-Host "⚠️  Esto eliminará TODOS los casos, mensajes y memorias. ¿Continuar? (s/N)"
if ($confirmation -notmatch '^[Ss]$') {
    Write-Host "❌ Operación cancelada" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📊 Conteo de registros antes de limpiar:" -ForegroundColor Yellow

$queryBefore = @"
SELECT 
    (SELECT COUNT(*) FROM cases) as cases,
    (SELECT COUNT(*) FROM messages) as messages,
    (SELECT COUNT(*) FROM memories WHERE kind IN ('immediate', 'session', 'episodic')) as memories,
    (SELECT COUNT(*) FROM semantic_knowledge) as knowledge_base;
"@

docker exec -it $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c $queryBefore

Write-Host ""
Write-Host "🗑️  Eliminando datos de prueba..." -ForegroundColor Yellow

# Eliminar en orden (respetando foreign keys)
$deleteScript = @"
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
"@

docker exec -it $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c $deleteScript

Write-Host ""
Write-Host "✅ Limpieza completada" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Conteo de registros después de limpiar:" -ForegroundColor Yellow

docker exec -it $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c $queryBefore

Write-Host ""
Write-Host "🎉 Base de datos lista para nuevas pruebas" -ForegroundColor Green
Write-Host "   ✓ Casos eliminados"
Write-Host "   ✓ Mensajes eliminados"
Write-Host "   ✓ Memorias de casos eliminadas"
Write-Host "   ✓ Base de conocimiento preservada"
Write-Host "   ✓ Usuarios preservados"
