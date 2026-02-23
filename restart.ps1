# 1) Configuración básica
$baseUrl = "http://localhost:8085"
$apiKey  = "defensoria-civil-2025-api-key"

$headers = @{
  "X-Api-Key" = $apiKey
}

# 2) (Opcional pero recomendable) Borrar la sesión 'default' si existe
try {
  Invoke-RestMethod -Uri "$baseUrl/api/sessions/default" `
                    -Headers $headers `
                    -Method Delete `
                    -ErrorAction Stop | Out-Null
  Write-Host "Sesión 'default' eliminada (si existía)." -ForegroundColor Yellow
} catch {
  Write-Host "Sesión 'default' no existía o ya estaba eliminada." -ForegroundColor Yellow
}

# 3) Crear de nuevo la sesión 'default' con webhook al backend
$body = @{
  name   = "default"
  config = @{
    webhooks = @(
      @{
        url    = "http://api:8000/webhook/whatsapp"
        events = @("message", "message.any", "session.status")
      }
    )
  }
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod -Uri "$baseUrl/api/sessions" `
                              -Headers $headers `
                              -Method Post `
                              -ContentType "application/json" `
                              -Body $body

Write-Host "Sesión creada:" -ForegroundColor Green
$response