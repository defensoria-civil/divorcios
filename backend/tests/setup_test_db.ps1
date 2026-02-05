# Script para configurar base de datos de test PostgreSQL
# Uso: .\setup_test_db.ps1

$ErrorActionPreference = "Continue"

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "Configuración de Base de Datos de Test" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Configuración
$DB_NAME = "def_civil_test"
$DB_USER = "postgres"
$DB_PASSWORD = "postgres"
$DB_HOST = "localhost"
$DB_PORT = "5432"

# Función para ejecutar comando SQL
function Invoke-PostgresSQL {
    param (
        [string]$Command,
        [string]$Database = "postgres"
    )
    
    $env:PGPASSWORD = $DB_PASSWORD
    $result = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $Database -c $Command 2>&1
    return $result
}

# Verificar si PostgreSQL está instalado
Write-Host "`n[1/5] Verificando instalación de PostgreSQL..." -ForegroundColor Yellow

try {
    $pgVersion = psql --version
    Write-Host "  ✓ PostgreSQL encontrado: $pgVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ ERROR: PostgreSQL no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host "    Instala PostgreSQL desde: https://www.postgresql.org/download/" -ForegroundColor Yellow
    exit 1
}

# Verificar si el servidor está corriendo
Write-Host "`n[2/5] Verificando servidor PostgreSQL..." -ForegroundColor Yellow

$env:PGPASSWORD = $DB_PASSWORD
$serverTest = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "SELECT 1;" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ ERROR: No se puede conectar al servidor PostgreSQL" -ForegroundColor Red
    Write-Host "    Verifica que el servidor esté corriendo:" -ForegroundColor Yellow
    Write-Host "    - Windows: Servicios -> PostgreSQL" -ForegroundColor Yellow
    Write-Host "    - Docker: docker-compose up -d db" -ForegroundColor Yellow
    exit 1
}

Write-Host "  ✓ Servidor PostgreSQL activo" -ForegroundColor Green

# Eliminar base de datos existente (si existe)
Write-Host "`n[3/5] Eliminando base de datos existente (si existe)..." -ForegroundColor Yellow

$dropResult = Invoke-PostgresSQL -Command "DROP DATABASE IF EXISTS $DB_NAME;"
Write-Host "  ✓ Base de datos anterior eliminada" -ForegroundColor Green

# Crear nueva base de datos
Write-Host "`n[4/5] Creando base de datos '$DB_NAME'..." -ForegroundColor Yellow

$createResult = Invoke-PostgresSQL -Command "CREATE DATABASE $DB_NAME ENCODING 'UTF8';"

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Base de datos '$DB_NAME' creada exitosamente" -ForegroundColor Green
} else {
    Write-Host "  ✗ ERROR al crear base de datos" -ForegroundColor Red
    Write-Host "  $createResult" -ForegroundColor Red
    exit 1
}

# Crear extensión pgvector
Write-Host "`n[5/5] Creando extensión pgvector..." -ForegroundColor Yellow

$vectorResult = Invoke-PostgresSQL -Command "CREATE EXTENSION IF NOT EXISTS vector;" -Database $DB_NAME

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Extensión pgvector creada" -ForegroundColor Green
} else {
    Write-Host "  ⚠ WARNING: No se pudo crear extensión pgvector" -ForegroundColor Yellow
    Write-Host "    Esto es normal si no tienes pgvector instalado" -ForegroundColor Yellow
    Write-Host "    Los tests funcionarán con SQLite como fallback" -ForegroundColor Yellow
}

# Resumen
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "CONFIGURACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "`nDetalles de conexión:" -ForegroundColor White
Write-Host "  Host:     $DB_HOST" -ForegroundColor Gray
Write-Host "  Puerto:   $DB_PORT" -ForegroundColor Gray
Write-Host "  Usuario:  $DB_USER" -ForegroundColor Gray
Write-Host "  Database: $DB_NAME" -ForegroundColor Gray
Write-Host "`nURL de conexión:" -ForegroundColor White
Write-Host "  postgresql+psycopg2://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}" -ForegroundColor Cyan

Write-Host "`nPara ejecutar tests:" -ForegroundColor White
Write-Host "  cd backend" -ForegroundColor Gray
Write-Host "  `$env:PYTHONPATH=`"C:\Users\spereyra\CODE\PROYECTOS\defensoria-civil\divorcios\backend\src`"" -ForegroundColor Gray
Write-Host "  python -m pytest tests/ -v" -ForegroundColor Gray

Write-Host "`n✓ Listo para ejecutar tests!" -ForegroundColor Green
Write-Host ""
