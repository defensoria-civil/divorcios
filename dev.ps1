$ErrorActionPreference = 'Continue'

# Ir a la raíz del repo
Set-Location -Path $PSScriptRoot

Write-Host "→ Iniciando entorno de desarrollo híbrido (Backend Local + Servicios Docker)..." -ForegroundColor Cyan

# 1. Detener contenedores que pueden causar conflictos (API ocupa puerto 8000)
Write-Host "→ Deteniendo contenedores de aplicación (API, Worker) para evitar conflictos..." -ForegroundColor Cyan
docker compose stop api worker 2>&1 | Out-Null

# 2. Levantar servicios de infraestructura (DB, Redis, WAHA)
Write-Host "→ Levantando servicios (DB, Redis, WAHA) en Docker..." -ForegroundColor Cyan

# Usar host.docker.internal para que WAHA pueda acceder al backend local
$webhookUrl = "http://host.docker.internal:8000/webhook/whatsapp"
Write-Host "   Configurando webhook: $webhookUrl" -ForegroundColor Gray

# Crear docker-compose.dev.yml con la configuración correcta
$devComposeContent = @"
version: "3.9"
services:
  waha:
    environment:
      - WAHA_WEBHOOK_URL=$webhookUrl
"@
$devComposeContent | Out-File -FilePath "$PSScriptRoot/docker-compose.dev.yml" -Encoding UTF8

# Levantar servicios usando el override
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db redis waha 2>&1 | Out-Null

# 3. Cargar variables de entorno desde .env
if (Test-Path "$PSScriptRoot/.env") {
    Write-Host "→ Cargando variables de entorno desde .env..." -ForegroundColor Cyan
    Get-Content "$PSScriptRoot/.env" | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [System.Environment]::SetEnvironmentVariable($name, $value, [System.EnvironmentVariableTarget]::Process)
        }
    }
}
else {
    Write-Warning "No se encontró archivo .env"
}

# 4. Sobrescribir variables para conexión local (localhost)
Write-Host "→ Configurando conexión a servicios locales..." -ForegroundColor Cyan

[System.Environment]::SetEnvironmentVariable("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5433/def_civil", [System.EnvironmentVariableTarget]::Process)
[System.Environment]::SetEnvironmentVariable("REDIS_URL", "redis://localhost:6380/0", [System.EnvironmentVariableTarget]::Process)
[System.Environment]::SetEnvironmentVariable("WAHA_BASE_URL", "http://localhost:3000", [System.EnvironmentVariableTarget]::Process)
[System.Environment]::SetEnvironmentVariable("WAHA_API_URL", "http://localhost:3000", [System.EnvironmentVariableTarget]::Process)

$env:PYTHONPATH = "$PSScriptRoot/backend/src"

# 5. Verificar entorno virtual
$venvPath = "$PSScriptRoot/backend/venv"
if (Test-Path $venvPath) {
    Write-Host "→ Usando entorno virtual en $venvPath" -ForegroundColor Green
    $pythonExe = "$venvPath/Scripts/python.exe"
    $uvicornExe = "$venvPath/Scripts/uvicorn.exe"
}
else {
    Write-Warning "No se encontró entorno virtual en backend/venv. Usando python del sistema."
    $pythonExe = "python"
    $uvicornExe = "uvicorn"
}

# 6. Iniciar Frontend en ventana separada
$frontendDir = "$PSScriptRoot/frontend"
if (Test-Path $frontendDir) {
    Write-Host "→ Verificando Frontend..." -ForegroundColor Cyan
    
    if (-not (Test-Path "$frontendDir/node_modules")) {
        Write-Host "→ Instalando dependencias del frontend..." -ForegroundColor Yellow
        Push-Location $frontendDir
        npm install
        Pop-Location
    }
    
    Write-Host "→ Iniciando Frontend en nueva ventana..." -ForegroundColor Green
    Start-Process -WorkingDirectory $frontendDir -FilePath "pwsh" -ArgumentList "-NoExit", "-Command", "npm run dev"
    Write-Host "   Frontend: http://localhost:5173" -ForegroundColor Gray
}
else {
    Write-Warning "No se encontró directorio frontend/"
}

# 7. Ejecutar Backend (en esta ventana)
Write-Host "→ Iniciando Backend (Uvicorn) con Hot-Reload..." -ForegroundColor Green
Write-Host "   API disponible en http://localhost:8000"
Write-Host "   Presiona Ctrl+C para detener."

Set-Location -Path "$PSScriptRoot/backend"

& $uvicornExe presentation.api.main:app --reload --host 0.0.0.0 --port 8000
