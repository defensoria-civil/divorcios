<#
.SYNOPSIS
    Limpia usuarios y casos del proyecto Divorcios en la VPS.

.DESCRIPTION
    Se conecta via SSH a la VPS y ejecuta TRUNCATE CASCADE sobre las tablas
    'cases' y 'users' (CASCADE limpia automaticamente messages, memories, etc.)

.EXAMPLE
    .\reset_vps_db.ps1    # Limpia casos, usuarios y datos asociados
#>

# --- Configuracion ---
$VPS_KEY = "$env:USERPROFILE\.gemini\antigravity\scratch\vps_final_key"
$VPS_HOST = "root@149.50.132.23"
$SSH_OPTS = "-i", $VPS_KEY, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"
$DB_CONTAINER = "divorcios-divorciosstack-krstoi-db-1"
$DB_USER = "postgres"
$DB_NAME = "def_civil"

# Tablas principales a limpiar (CASCADE borra las dependientes: messages, memories, etc.)
$tables = @("cases", "users")

# --- Banner ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESET DB - Divorcios VPS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Verificar conexion ---
Write-Host "[1/3] Verificando conexion SSH..." -ForegroundColor Gray
$testResult = & ssh @SSH_OPTS $VPS_HOST "echo ok" 2>&1
if ($testResult -ne "ok") {
    Write-Host "  ERROR: No se pudo conectar." -ForegroundColor Red
    exit 1
}
Write-Host "  OK" -ForegroundColor Green

# --- Mostrar estado actual ---
Write-Host "[2/3] Estado actual:" -ForegroundColor Gray
$allTables = @("users", "cases", "messages", "memories", "semantic_knowledge", "support_documents")
foreach ($t in $allTables) {
    $count = & ssh @SSH_OPTS $VPS_HOST "docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c 'SELECT count(*) FROM $t;'" 2>&1
    $count = ($count -join "").Trim()
    Write-Host "  $t : $count registros" -ForegroundColor White
}

# --- Confirmacion ---
Write-Host ""
Write-Host "Se van a eliminar: cases, users (y dependientes: messages, memories, etc.)" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Escribi 'RESET' para confirmar"
if ($confirm -ne "RESET") {
    Write-Host "Cancelado." -ForegroundColor Yellow
    exit 0
}

# --- Ejecutar ---
Write-Host ""
Write-Host "[3/3] Limpiando..." -ForegroundColor Gray
$sql = "BEGIN; TRUNCATE TABLE cases CASCADE; TRUNCATE TABLE users CASCADE; COMMIT;"
$result = & ssh @SSH_OPTS $VPS_HOST "docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c `"$sql`"" 2>&1
$resultText = $result -join "`n"

if ($resultText -match "COMMIT") {
    Write-Host "  Listo! Base de datos limpiada." -ForegroundColor Green
    Write-Host ""
    Write-Host "  Estado final:" -ForegroundColor Gray
    foreach ($t in $allTables) {
        $count = & ssh @SSH_OPTS $VPS_HOST "docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c 'SELECT count(*) FROM $t;'" 2>&1
        $count = ($count -join "").Trim()
        Write-Host "    $t : $count" -ForegroundColor White
    }
}
else {
    Write-Host "  ERROR: $resultText" -ForegroundColor Red
    exit 1
}

Write-Host ""
