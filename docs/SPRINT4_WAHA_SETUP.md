# Sprint 4 - Configuración WAHA y Pruebas End-to-End

## 📋 Objetivo

Configurar WAHA (WhatsApp HTTP API) para probar el flujo completo de procesamiento de mensajes e imágenes vía WhatsApp.

---

## 🐳 Paso 1: Configurar WAHA con Docker

### 1.1 Crear archivo docker-compose para WAHA

En la raíz del proyecto (`divorcios/`), crea o actualiza `docker-compose.waha.yml`:

```yaml
version: '3.8'

services:
  waha:
    image: devlikeapro/waha:latest
    container_name: waha-whatsapp
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      # API Security
      - WHATSAPP_API_KEY=your-secure-api-key-123
      
      # Webhook Configuration
      - WHATSAPP_HOOK_URL=http://host.docker.internal:8000/api/webhook/whatsapp
      - WHATSAPP_HOOK_EVENTS=message,message.any
      
      # Session Configuration
      - WHATSAPP_START_SESSION=default
      
      # Storage for session data
    volumes:
      - waha_sessions:/app/.sessions
    networks:
      - waha-network

networks:
  waha-network:
    driver: bridge

volumes:
  waha_sessions:
```

### 1.2 Iniciar WAHA

```bash
# Desde la raíz del proyecto
docker-compose -f docker-compose.waha.yml up -d
```

### 1.3 Verificar que WAHA está corriendo

```bash
# Ver logs
docker logs waha-whatsapp

# Verificar API
curl http://localhost:3000/api/sessions
```

Deberías ver algo como:
```json
[
  {
    "name": "default",
    "status": "SCAN_QR_CODE"
  }
]
```

---

## 📱 Paso 2: Conectar WhatsApp

### 2.1 Obtener QR Code

```bash
# Obtener QR para escanear
curl http://localhost:3000/api/default/auth/qr
```

O visita en el navegador:
```
http://localhost:3000/api/default/auth/qr
```

### 2.2 Escanear con WhatsApp

1. Abre WhatsApp en tu móvil
2. Ve a **Configuración > Dispositivos vinculados**
3. **Vincular un dispositivo**
4. Escanea el QR code mostrado

### 2.3 Verificar conexión

```bash
curl http://localhost:3000/api/sessions
```

Debería mostrar:
```json
[
  {
    "name": "default",
    "status": "WORKING"
  }
]
```

---

## ⚙️ Paso 3: Configurar Backend

### 3.1 Actualizar variables de entorno

En `backend/.env` o `backend/.env.local`:

```env
# WAHA Configuration
WAHA_BASE_URL=http://localhost:3000
WAHA_API_KEY=your-secure-api-key-123

# Asegurar que otros servicios estén configurados
OLLAMA_CLOUD_API_KEY=tu_api_key
GEMINI_API_KEY=tu_api_key

# Database (si no usas Docker)
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/def_civil
```

### 3.2 Iniciar Backend

```bash
cd backend
uv run python -m app.main
```

Backend debería estar en: `http://localhost:8000`

---

## 🧪 Paso 4: Pruebas End-to-End

### Test 4.1: Mensaje de Texto Simple

**Acción:** Envía un mensaje de WhatsApp al número conectado

```
Hola
```

**Resultado Esperado:**
- ✅ Backend recibe webhook
- ✅ Bot responde con saludo
- ✅ Se crea un nuevo caso en la BD
- ✅ Logs muestran: `whatsapp_inbound`

**Verificar en logs:**
```bash
# Ver logs del backend
tail -f backend/logs/app.log
```

---

### Test 4.2: Envío de Datos Personales

**Acción:** Responde al bot con tus datos

```
Mi nombre es Juan Pérez
DNI 12345678
```

**Resultado Esperado:**
- ✅ Bot extrae nombre y DNI
- ✅ Actualiza el caso en la BD
- ✅ Responde confirmando los datos

**Verificar en Dashboard:**
1. Ir a `http://localhost:5173/cases`
2. Ver caso creado con nombre "Juan Pérez"
3. DNI debe ser "12345678"

---

### Test 4.3: Envío de Imagen (DNI)

**Acción:** Envía una foto del DNI por WhatsApp

1. Toma foto del DNI (frente o dorso)
2. Envíala por WhatsApp

**Resultado Esperado:**
- ✅ Backend detecta imagen: `image_received`
- ✅ Descarga imagen via WAHA API
- ✅ Ejecuta OCR multi-provider (Ollama Vision → Gemini fallback)
- ✅ Extrae datos: nombre, DNI, fecha_nacimiento, domicilio
- ✅ Actualiza caso automáticamente
- ✅ Responde confirmando datos extraídos

**Verificar logs:**
```bash
# Buscar en logs
grep "image_received" backend/logs/app.log
grep "ocr_extraction" backend/logs/app.log
grep "case_updated" backend/logs/app.log
```

**Verificar en Dashboard:**
1. Refrescar vista de casos
2. Ver datos actualizados del DNI
3. Verificar campos: nombre, DNI, fecha_nacimiento, domicilio

---

### Test 4.4: Envío de Imagen (Partida de Matrimonio)

**Acción:** Envía foto de la partida de matrimonio

**Resultado Esperado:**
- ✅ OCR extrae: fecha_matrimonio, lugar_matrimonio
- ✅ Caso actualizado con datos matrimoniales
- ✅ Bot confirma extracción

**Verificar en Dashboard:**
1. Ir a detalle del caso
2. Ver sección "Datos del Matrimonio"
3. Verificar fecha y lugar de matrimonio

---

### Test 4.5: Generación de PDF

**Acción:** Una vez completados los datos, pide al bot generar el PDF

```
Generar demanda
```

**Resultado Esperado:**
- ✅ Backend genera PDF con datos del caso
- ✅ Envía PDF por WhatsApp
- ✅ Usuario recibe archivo adjunto

**Verificar:**
1. Abrir PDF recibido en WhatsApp
2. Ver que contiene:
   - Nombre completo
   - DNI
   - Domicilio
   - Datos del matrimonio
   - Texto legal de demanda de divorcio

---

### Test 4.6: Conversación Completa (Flujo Ideal)

**Script de prueba:**

```
Usuario: Hola
Bot: [Saludo y explicación del proceso]

Usuario: Mi nombre es María López, DNI 87654321
Bot: [Confirma datos]

Usuario: [Envía foto del DNI]
Bot: [Confirma extracción automática de datos]

Usuario: [Envía foto de partida de matrimonio]
Bot: [Confirma datos matrimoniales]

Usuario: Generar demanda
Bot: [Genera y envía PDF]
```

**Resultado Esperado:**
- ✅ Flujo completo sin errores
- ✅ Caso con todos los datos completos
- ✅ PDF generado y entregado
- ✅ Estado del caso: `documentacion_completa`

---

## 🔍 Paso 5: Debugging y Troubleshooting

### Problema: WAHA no responde

**Solución:**
```bash
# Verificar contenedor
docker ps | grep waha

# Reiniciar WAHA
docker restart waha-whatsapp

# Ver logs
docker logs waha-whatsapp -f
```

### Problema: QR code expirado

**Solución:**
```bash
# Obtener nuevo QR
curl http://localhost:3000/api/default/auth/qr

# O resetear sesión
docker restart waha-whatsapp
```

### Problema: Webhook no llega al backend

**Verificación:**
```bash
# Test manual del webhook
curl -X POST http://localhost:8000/api/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{
      "from": "5491234567890",
      "body": "test",
      "type": "chat",
      "chatId": "5491234567890@c.us"
    }]
  }'
```

**Solución:**
- Verificar firewall
- Asegurar que backend esté corriendo en puerto 8000
- Verificar `WHATSAPP_HOOK_URL` en docker-compose

### Problema: OCR no funciona

**Verificación:**
```bash
# Test de providers
cd backend
uv run python -c "
from infrastructure.ai.ocr_service_impl import MultiProviderOCRService
import asyncio

async def test():
    ocr = MultiProviderOCRService()
    result = await ocr.extract_from_image(open('test_dni.jpg', 'rb').read(), 'dni')
    print(result)

asyncio.run(test())
"
```

**Solución:**
- Verificar API keys: `OLLAMA_CLOUD_API_KEY`, `GEMINI_API_KEY`
- Verificar logs para ver qué provider está fallando
- Asegurar que la imagen sea legible

### Problema: Backend no puede descargar imagen de WAHA

**Solución:**
```bash
# Verificar conectividad
curl http://localhost:3000/api/files/{media_id} \
  -H "X-Api-Key: your-secure-api-key-123"
```

- Verificar que `WAHA_API_KEY` coincida en ambos lados
- Asegurar que el `media_id` sea correcto en los logs

---

## 📊 Métricas de Éxito

### Criterios de Aceptación

- [ ] WAHA conectado y funcionando
- [ ] WhatsApp vinculado y estado: `WORKING`
- [ ] Backend recibe webhooks correctamente
- [ ] Bot responde a mensajes de texto
- [ ] OCR extrae datos de imágenes correctamente
- [ ] Casos se actualizan automáticamente
- [ ] PDF se genera y envía correctamente
- [ ] Flujo completo sin errores manuales

### Performance Esperado

- **Tiempo de respuesta texto:** < 2 segundos
- **Tiempo OCR (DNI):** 5-10 segundos
- **Tiempo OCR (Partida):** 10-15 segundos
- **Generación PDF:** < 3 segundos
- **Envío documento WhatsApp:** 5-10 segundos

---

## 🗂️ Estructura de Archivos

```
divorcios/
├── docker-compose.waha.yml       # Configuración de WAHA
├── backend/
│   ├── .env                      # Variables de entorno
│   ├── src/
│   │   ├── infrastructure/
│   │   │   ├── messaging/
│   │   │   │   └── waha_service_impl.py  # Cliente WAHA
│   │   │   └── ai/
│   │   │       └── ocr_service_impl.py   # OCR multi-provider
│   │   └── presentation/
│   │       └── api/
│   │           └── routes/
│   │               └── webhook.py        # Endpoint webhook
│   └── logs/
│       └── app.log                       # Logs de procesamiento
└── docs/
    └── SPRINT4_WAHA_SETUP.md            # Esta guía
```

---

## 🚀 Comandos Rápidos

```bash
# Iniciar todo el stack
docker-compose -f docker-compose.waha.yml up -d
cd backend && uv run python -m app.main &
cd frontend && npm run dev &

# Verificar estado
curl http://localhost:3000/api/sessions  # WAHA
curl http://localhost:8000/health        # Backend
curl http://localhost:5173               # Frontend

# Ver logs en tiempo real
docker logs waha-whatsapp -f              # WAHA
tail -f backend/logs/app.log              # Backend

# Detener todo
docker-compose -f docker-compose.waha.yml down
pkill -f "python -m app.main"
pkill -f "npm run dev"
```

---

## 📝 Próximos Pasos

Una vez completadas las pruebas:

1. ✅ Documentar casos de prueba exitosos
2. ✅ Tomar screenshots del flujo completo
3. ✅ Medir tiempos de respuesta reales
4. 🔄 Ajustar prompts si es necesario
5. 🔄 Optimizar timeouts de OCR
6. 🚀 Preparar para staging/producción

---

## 🎯 Estado Actual del Proyecto

Después de completar Sprint 4:

- **Frontend:** ✅ 100% funcional
- **Backend:** ✅ 100% funcional
- **Base de Conocimiento:** ✅ Cargada
- **WhatsApp Bot:** ✅ Configurado
- **Procesamiento Imágenes:** ✅ Implementado
- **Flujo End-to-End:** 🔄 En pruebas

**Progreso General:** **95%** (meta final)

---

## 📞 Soporte

Para problemas específicos:
1. Revisar logs: `backend/logs/app.log`
2. Verificar estado WAHA: `http://localhost:3000/api/sessions`
3. Probar webhook manualmente con curl
4. Verificar API keys en `.env`

**Sistema listo para pruebas de aceptación del usuario.** ✅
