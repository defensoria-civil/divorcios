# Procesamiento de Imágenes - Documentación

## Resumen

Se ha implementado el procesamiento automático de imágenes (DNI y actas de matrimonio) enviadas por usuarios a través de WhatsApp, utilizando OCR con Gemini Vision para extracción inteligente de datos.

## Arquitectura

### Flujo de Procesamiento

```
Usuario envía imagen → Webhook recibe mensaje
    ↓
Webhook detecta type='image' y extrae mediaId
    ↓
Use Case recibe IncomingMessageRequest con media_id
    ↓
Use Case descarga imagen desde WhatsApp (WAHA API)
    ↓
Use Case determina tipo de documento según fase del caso
    ↓
OCR Service (Gemini) procesa imagen y extrae datos estructurados
    ↓
Use Case actualiza caso con datos extraídos
    ↓
Use Case responde al usuario con confirmación
```

### Componentes Implementados

#### 1. **Modelo de Datos** (`models.py`)

Campos agregados al modelo `Case`:
```python
dni_image_url = Column(String(255))        # Referencia media_id del DNI
marriage_cert_url = Column(String(255))    # Referencia media_id del acta
fecha_matrimonio = Column(Date)            # Fecha extraída del acta
lugar_matrimonio = Column(String(255))     # Lugar extraído del acta
```

#### 2. **OCR Service** (`gemini_ocr_service_impl.py`)

Ya estaba implementado con tres métodos:

- `extract_dni_data(image_bytes)`: Extrae datos de DNI argentino
  - Número de documento
  - Nombre completo
  - Fecha de nacimiento
  - Sexo
  - Fecha de emisión

- `extract_marriage_certificate_data(image_bytes)`: Extrae datos de acta de matrimonio
  - Fecha de matrimonio
  - Lugar de matrimonio
  - Nombres de cónyuges
  - Datos de registro civil (acta, tomo, folio)

- `extract_generic_document(image_bytes)`: Extrae texto completo

**Características:**
- Validación automática de datos extraídos
- Score de confianza (confidence)
- Lista de errores detectados
- Prompts optimizados para documentos argentinos

#### 3. **WhatsApp Service** (`waha_service_impl.py`)

Ya incluía método de descarga:
```python
async def download_media(media_id: str) -> bytes
```

#### 4. **Use Case** (`process_incoming_message.py`)

Métodos agregados:

**`_handle_media(case, media_id)`**
- Descarga imagen desde WhatsApp
- Determina tipo de documento según fase del caso
- Delega a procesadores específicos

**`_process_dni_image(case, image_bytes, media_id)`**
- Ejecuta OCR para DNI
- Valida confidence (mínimo 0.6)
- Actualiza datos del caso: dni, nombre, fecha_nacimiento
- Guarda referencia en dni_image_url
- Avanza fase si corresponde
- Responde con confirmación y datos detectados

**`_process_marriage_cert_image(case, image_bytes, media_id)`**
- Ejecuta OCR para acta de matrimonio
- Valida confidence (mínimo 0.6)
- Actualiza datos del caso: fecha_matrimonio, lugar_matrimonio
- Guarda referencia en marriage_cert_url
- Actualiza status a "documentacion_completa"
- Genera resumen episódico
- Responde con confirmación y próximos pasos

**Lógica de detección de tipo:**
- Si fase = "dni" → procesar como DNI
- Si fase = "documentacion" y no tiene dni_image_url → procesar como DNI
- Si fase = "documentacion" y ya tiene dni_image_url → procesar como acta
- Otras fases → rechazar imagen

#### 5. **Webhook** (`webhook.py`)

Ya estaba implementado correctamente:
```python
# Detecta tipo de mensaje
media_id = None
if msg.type == 'image' and msg.mediaId:
    media_id = msg.mediaId

# Crea request con media_id
request = IncomingMessageRequest(
    phone=phone,
    text=text,
    media_id=media_id
)
```

#### 6. **Schema** (`webhook.py`)

Ya incluía campos de media:
```python
class WhatsAppMessage(BaseModel):
    type: Optional[str]       # 'text', 'image', etc.
    mediaId: Optional[str]    # ID del archivo
    mediaUrl: Optional[str]   # URL si disponible
    mimeType: Optional[str]   # Tipo MIME
    caption: Optional[str]    # Leyenda de imagen
```

## Scripts de Migración

### Script creado: `migrate_add_document_fields.py`

Agrega los 4 campos nuevos a la tabla `cases`:
- dni_image_url
- marriage_cert_url
- fecha_matrimonio
- lugar_matrimonio

**Uso:**
```bash
# Local
python backend/scripts/migrate_add_document_fields.py

# Docker
docker compose exec api python /app/backend/scripts/migrate_add_document_fields.py
```

**Características:**
- Usa `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (idempotente)
- No pierde datos existentes
- Logging completo de operaciones

## Configuración Requerida

### Variables de Entorno

```bash
# En .env
GEMINI_API_KEY=tu_api_key_aqui    # Para OCR con Gemini Vision
WAHA_BASE_URL=http://waha:3000    # URL del servicio WhatsApp
WAHA_API_KEY=changeme              # API key de WAHA
```

### Dependencias

Ya instaladas en requirements.txt:
- google-generativeai (Gemini)
- Pillow (procesamiento de imágenes)
- httpx (cliente HTTP async)

## Ejemplo de Flujo Completo

### 1. Usuario en Fase DNI

**Usuario:** [envía foto de DNI]

**Sistema:**
- Webhook recibe mensaje con type='image', mediaId='abc123'
- Use case detecta media_id
- Descarga imagen desde WhatsApp
- Ejecuta OCR con Gemini
- Extrae: DNI=12345678, Nombre="JUAN PEREZ"
- Actualiza caso con datos
- Guarda referencia dni_image_url='abc123'

**Respuesta al usuario:**
```
✅ DNI procesado correctamente.

**Datos detectados:**
- DNI: 12345678
- Nombre: JUAN PEREZ

¿Los datos son correctos? Si hay algún error, decime cuál es para corregirlo.
```

### 2. Usuario en Fase Documentación

**Primera imagen (DNI):**
- Sistema detecta que no tiene dni_image_url
- Procesa como DNI
- Responde con confirmación

**Segunda imagen (Acta):**
- Sistema detecta que ya tiene dni_image_url
- Procesa como acta de matrimonio
- Extrae fecha y lugar de matrimonio
- Marca status='documentacion_completa'

**Respuesta al usuario:**
```
✅ Acta de matrimonio procesada correctamente.

**Datos detectados:**
- Fecha matrimonio: 15/06/2018
- Lugar: San Rafael, Mendoza

🎉 **¡Documentación completa!**

Ya tengo toda la información necesaria. En las próximas 48hs un operador de la Defensoría 
va a revisar tu caso y te va a contactar para coordinar los siguientes pasos.

¿Tenés alguna consulta mientras tanto?
```

## Manejo de Errores

### Imagen poco clara (confidence < 0.6)

```
No pude procesar el DNI correctamente:
- Número de documento no válido o no detectado
- Fecha de nacimiento no válida

Por favor, enviá una foto más clara del DNI (frente y dorso).
```

### Error de descarga de media

```
Disculpá, tuve un problema procesando la imagen. ¿Podés intentar enviarla de nuevo?
```

### Imagen en fase incorrecta

```
Gracias por la imagen, pero todavía no estamos en la etapa de documentación. 
Primero necesito completar tus datos personales.
```

## Próximos Pasos (Sprint 2+)

- [ ] Almacenamiento permanente de imágenes (S3/Cloud Storage)
- [ ] Validación cruzada de datos (DNI vs datos ingresados manualmente)
- [ ] Soporte para PDFs
- [ ] Soporte para múltiples páginas
- [ ] Dashboard para revisar imágenes procesadas
- [ ] Reintento automático con OCR alternativo si falla Gemini
- [ ] Tests de integración para flujo completo

## Testing

### Manual Testing

1. Iniciar servicios:
```bash
docker compose up -d
```

2. Ejecutar migración:
```bash
docker compose exec api python /app/backend/scripts/migrate_add_document_fields.py
```

3. Enviar mensaje de texto para iniciar caso
4. Avanzar hasta fase DNI o documentación
5. Enviar imagen de DNI
6. Verificar respuesta con datos extraídos
7. Enviar imagen de acta de matrimonio
8. Verificar respuesta final

### Logs a Monitorear

```python
# Logs relevantes
"downloading_media"              # Inicio descarga
"whatsapp_media_downloaded"      # Descarga exitosa
"processing_dni_image"           # Inicio OCR DNI
"dni_ocr_completed"              # OCR DNI completado
"processing_marriage_cert"       # Inicio OCR acta
"marriage_cert_ocr_completed"    # OCR acta completado
"media_processing_error"         # Error general
```

## Notas Técnicas

1. **Idempotencia**: El sistema puede recibir la misma imagen múltiples veces sin duplicar datos.

2. **Media IDs**: Los mediaId de WAHA son únicos y sirven como referencia permanente.

3. **Async/Await**: Todo el flujo es asíncrono para no bloquear el webhook.

4. **Confidence Threshold**: Se usa 0.6 como mínimo aceptable. Valores mayores a 0.8 muestran ✅, menores muestran ⚠️.

5. **Memoria**: Los datos extraídos se guardan tanto en el modelo Case como en la memoria contextual del sistema.

## Soporte

Para problemas o consultas:
- Revisar logs con structlog
- Verificar que Gemini API key esté configurada
- Verificar que WAHA esté respondiendo
- Revisar que las imágenes sean legibles (no borrosas, buena iluminación)
