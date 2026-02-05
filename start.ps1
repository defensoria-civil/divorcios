$ErrorActionPreference = 'Stop'

# Ir a la raíz del repo (donde está este script)
Set-Location -Path $PSScriptRoot

function Wait-Port {
  param(
    [int]$Port,
    [int]$TimeoutSeconds = 180,
    [string]$Name = "Servicio"
  )
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
    try {
      $ok = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet
      if ($ok) { return $true }
    } catch {}
    Start-Sleep -Seconds 2
  }
  Write-Warning "Tiempo de espera agotado esperando $Name en puerto $Port"
  return $false
}

function Wait-HttpOk {
  param(
    [string]$Url,
    [int]$TimeoutSeconds = 180,
    [string]$Name = "Servicio"
  )
  $sw = [Diagnostics.Stopwatch]::StartNew()
  while ($sw.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
    try {
      $r = Invoke-WebRequest -UseBasicParsing -Method GET -Uri $Url -TimeoutSec 5
      if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 300) { return $true }
    } catch {}
    Start-Sleep -Seconds 2
  }
  Write-Warning "Tiempo de espera agotado esperando $Name en $Url"
  return $false
}

Write-Host "→ Verificando Docker..." -ForegroundColor Cyan
try {
  docker info | Out-Null
} catch {
  Write-Error "Docker no está instalado o no está corriendo. Abre Docker Desktop e inténtalo de nuevo."
  exit 1
}

# Asegurar .env
if (-not (Test-Path "$PSScriptRoot/.env")) {
  Write-Warning ".env no encontrado. Crea y completa variables necesarias antes de continuar."
}

# Construir lista de archivos de compose (base + override opcional para WAHA)
$composeFiles = @("$PSScriptRoot/docker-compose.yml")
if (Test-Path "$PSScriptRoot/docker-compose.waha.yml") {
  $composeFiles += "$PSScriptRoot/docker-compose.waha.yml"
}

# Armar y ejecutar docker compose (con build por defecto)
$composeArgs = @()
foreach ($f in $composeFiles) { $composeArgs += @('-f', $f) }
$composeArgs += @('up', '-d', '--build')

Write-Host "→ Levantando servicios con Docker Compose..." -ForegroundColor Cyan
Write-Host ("docker compose " + ($composeArgs -join ' ')) -ForegroundColor DarkGray

& docker compose @composeArgs
if ($LASTEXITCODE -ne 0) {
  Write-Error "Falló 'docker compose up'. Revisa los logs de Docker."
  exit $LASTEXITCODE
}

Write-Host "→ Esperando que servicios estén listos..." -ForegroundColor Cyan
# Health check variables utilized to avoid lint warnings
$apiReady  = Wait-HttpOk -Url 'http://localhost:8000/health/' -Name 'API'
$wahaReady = Wait-Port   -Port 8085 -Name 'WAHA'

if (-not $apiReady -or -not $wahaReady) {
    Write-Warning "Algunos servicios no están completamente listos. Revisa los logs."
}

Write-Host "✔ Infra lista: API, Worker, PostgreSQL, Redis, WAHA" -ForegroundColor Green
Write-Host "   - API:        http://localhost:8000"
Write-Host "   - Docs:       http://localhost:8000/docs"
Write-Host "   - PostgreSQL: localhost:5432"
Write-Host "   - Redis:      localhost:6379"
Write-Host "   - WAHA:       http://localhost:8085"

# Iniciar frontend automáticamente
$frontendDir = Join-Path $PSScriptRoot 'frontend'
if (-not (Test-Path $frontendDir)) {
  Write-Warning "No se encontró la carpeta 'frontend'. Saltando frontend."
} else {
  Write-Host "→ Verificando Node/NPM..." -ForegroundColor Cyan
  $npmOk = $true
  try { npm -v | Out-Null } catch { $npmOk = $false }
  if (-not $npmOk) {
    Write-Warning "NPM no está disponible. Instala Node.js para levantar el frontend. Continuando solo con backend."
  } else {
    if (-not (Test-Path (Join-Path $frontendDir 'node_modules'))) {
      Write-Host "→ Instalando dependencias del frontend (npm install)..." -ForegroundColor DarkYellow
      # Using Push-Location/Pop-Location instead of aliases pushd/popd
      Push-Location $frontendDir
      npm install
      $npmExit = $LASTEXITCODE
      Pop-Location
      if ($npmExit -ne 0) {
        Write-Warning "npm install falló ($npmExit). El frontend no se iniciará."
      }
    }
    if (Test-Path (Join-Path $frontendDir 'node_modules')) {
      Write-Host "→ Iniciando frontend (Vite) en una nueva ventana..." -ForegroundColor Cyan
      Start-Process -WorkingDirectory $frontendDir -FilePath "pwsh" -ArgumentList "-NoExit -Command npm run dev" | Out-Null
      Write-Host "✔ Frontend iniciado en http://localhost:5173" -ForegroundColor Green
    }
  }
}

# Abrir URLs útiles
try { Start-Process "http://localhost:8000/docs" | Out-Null } catch {}
try { Start-Process "http://localhost:5173" | Out-Null } catch {}

Write-Host "✅ Todo listo. Usa 'docker compose logs -f' para ver logs." -ForegroundColor Green
