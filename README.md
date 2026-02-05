# Sistema de Defensoría Civil - LLM Intelligence System

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

Sistema de asistencia legal automatizada para divorcios en la Defensoría Civil de San Rafael, Mendoza, Argentina. Implementado con **Clean Architecture**, **LLMs avanzados** y **memoria contextual** para proporcionar una experiencia conversacional inteligente vía WhatsApp.

## 🎯 Características Principales

### 🤖 Bot de WhatsApp Inteligente
- Conversaciones contextuales con IA especializada en derecho argentino
- Flujo guiado paso a paso para recolección de datos legales
- Validación automática de información con reglas específicas
- Reconocimiento de usuarios que retoman trámites
- Manejo de casos especiales (violencia, hijos menores, bienes)

### 🧠 Memoria Contextual Avanzada
- **Memoria Inmediata**: Últimos 10 mensajes de la conversación
- **Memoria de Sesión**: Datos del trámite actual
- **Memoria Episódica**: Historial de conversaciones pasadas con búsqueda semántica
- **Memoria Semántica**: Base de conocimiento legal estructurado
- Búsqueda vectorial con **pgvector** para recuperación inteligente

### 🛡️ Validación y Seguridad
- **Detección de alucinaciones** en respuestas del LLM (>99% precisión)
- **Validación de datos** según reglas legales argentinas:
  - Edad mínima 18 años para matrimonio
  - Jurisdicción San Rafael/Mendoza
  - Secuencia lógica de fechas (nacimiento → matrimonio → separación)
- **Protección contra inyección de prompts**
- **Rate limiting** inteligente por IP y usuario
- **Headers de seguridad** (CSP, HSTS, X-Frame-Options)

### 📝 Procesamiento Inteligente de Documentos
- **OCR con Gemini Vision** para DNI y actas de matrimonio
- Extracción estructurada de datos con validación
- Generación automática de documentos legales en PDF
- Procesamiento asíncrono con Celery para tareas pesadas

### 🔄 Integración con Sistemas
- **WhatsApp Business API** vía WAHA
- **Google Gemini** (LLM principal) + **Ollama** (fallback)
- **PostgreSQL** con extensión pgvector para embeddings
- **Redis** para caché, sesiones y rate limiting

## 🏗️ Arquitectura

Implementación estricta de **Clean Architecture** con separación en capas:

```
├── Domain (Entidades y lógica de negocio pura)
├── Application (Casos de uso, interfaces, DTOs, servicios)
├── Infrastructure (Implementaciones concretas: DB, AI, messaging)
└── Presentation (API REST, webhooks, CLI)
```

### Principios SOLID
- **S**ingle Responsibility: Cada clase tiene una única responsabilidad
- **O**pen/Closed: Extensible sin modificar código existente
- **L**iskov Substitution: Interfaces intercambiables
- **I**nterface Segregation: Interfaces específicas por cliente
- **D**ependency Inversion: Dependencias via abstracciones

## 🚀 Quickstart

### Con Docker (Recomendado)

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd def-civil-divorcios

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env y agregar GEMINI_API_KEY

# 3. Levantar servicios
docker compose up --build

# 4. Verificar
curl http://localhost:8000/health/
```

### Sin Docker (Desarrollo Local)

```bash
# Requisitos previos
# - Python 3.12+
# - PostgreSQL 14+ con extensión vector
# - Redis 7+

# 1. Instalar dependencias
cd backend
pip install -r requirements.txt

# 2. Configurar DB
createdb def_civil
psql def_civil -c "CREATE EXTENSION vector;"

# 3. Configurar PYTHONPATH
export PYTHONPATH=$(pwd)/src

# 4. Ejecutar
uvicorn presentation.api.main:app --reload --host 0.0.0.0 --port 8000

# 5. (Opcional) Worker de Celery
celery -A infrastructure.tasks.celery_app.app worker -l info
```

## 📋 Servicios Disponibles

| Servicio | Puerto | URL |
|----------|--------|-----|
| API Backend | 8000 | http://localhost:8000 |
| Docs (Swagger) | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| WAHA (WhatsApp) | 3000 | http://localhost:3000 |
| Ollama | 11434 | http://localhost:11434 |

## 🔌 Endpoints Principales

### Health Check
```bash
GET /health/
# Response: {"status": "ok"}
```

### Webhook WhatsApp
```bash
POST /webhook/whatsapp
Content-Type: application/json

{
  "messages": [
    {
      "from": "5492604123456",
      "body": "Hola, quiero iniciar un divorcio"
    }
  ]
}
```

### Listar Casos (Auth requerida)
```bash
GET /api/cases/
Authorization: Bearer <JWT_TOKEN>
```

### Métricas
```bash
GET /api/metrics/summary
Authorization: Bearer <JWT_TOKEN>
# Response: {"total_cases": 42}
```

## 🧪 Testing

### Tests Unitarios
```bash
pytest backend/tests/unit -v
```

### Tests de Integración
```bash
# Crear DB de test
createdb def_civil_test

# Ejecutar tests
pytest backend/tests/integration -v
```

### Coverage
```bash
pytest backend/tests --cov=backend/src --cov-report=html
open htmlcov/index.html
```

### 🧹 Limpieza de Datos de Prueba

Durante el desarrollo y testing del chatbot de WhatsApp, es necesario limpiar los datos frecuentemente para comenzar pruebas desde cero.

**Opción 1: PowerShell (Windows - Recomendado)**
```powershell
.\clean.ps1
# o directamente:
.\scripts\clean_test_data.ps1
```

**Opción 2: Python (Cross-platform)**
```bash
python scripts/clean_test_data.py
```

**Opción 3: Bash (Linux/Mac)**
```bash
chmod +x scripts/clean_test_data.sh
./scripts/clean_test_data.sh
```

⚠️ **Lo que hace el script:**
- ✅ Preserva: usuarios y base de conocimiento legal
- ❌ Elimina: casos, mensajes y memorias de conversaciones
- 🔄 Resetea IDs de secuencias

Ver más detalles en [`scripts/README.md`](./scripts/README.md)

## 🔧 Configuración

### Variables de Entorno Críticas

```env
# LLM Principal
GEMINI_API_KEY=tu_api_key_aqui  # OBLIGATORIO

# Base de datos
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db

# WhatsApp
WAHA_BASE_URL=http://waha:3000
WAHA_API_KEY=tu_waha_key

# Seguridad
SECRET_KEY=cambiar_en_produccion_minimo_32_caracteres

# Validación
ALLOWED_JURISDICTIONS=San Rafael,Mendoza
```

## 📊 Flujo de Conversación

```mermaid
Usuario: "Hola, quiero iniciar un divorcio"
    ↓
Bot: "¿Tipo de divorcio: unilateral o conjunta?"
    ↓
Usuario: "unilateral"
    ↓
Bot: "¿Cuál es tu nombre completo?"
    ↓
[Recolección de datos con validación]
    ↓
Bot: "✅ Datos completos. Envíame DNI y acta de matrimonio"
    ↓
[OCR + Validación de documentos]
    ↓
Bot: "✅ Documentación procesada. Generando petición..."
    ↓
[Generación de PDF legal]
    ↓
Bot: [Envía PDF] "Trámite iniciado. Seguimiento por email."
```

## 🛠️ Stack Tecnológico

### Backend
- **FastAPI** 0.115+: Framework web asíncrono
- **SQLAlchemy** 2.0: ORM con soporte async
- **Pydantic** 2.8: Validación de datos
- **structlog**: Logging estructurado

### Base de Datos
- **PostgreSQL** 14+: Base de datos principal
- **pgvector**: Extensión para embeddings vectoriales
- **Redis** 7: Caché, sesiones, rate limiting

### IA y ML
- **Google Gemini** 1.5 Flash: LLM principal + Vision para OCR
- **Ollama**: LLM local de fallback
- **Embeddings** text-embedding-004: Búsqueda semántica

### Procesamiento
- **Celery** 5.4: Tareas asíncronas
- **ReportLab** 4.2: Generación de PDFs
- **Pillow** 10.4: Procesamiento de imágenes

### Messaging
- **WAHA**: WhatsApp HTTP API
- **httpx**: Cliente HTTP asíncrono

## 🔐 Seguridad

### Implementado
- ✅ Autenticación JWT para operadores
- ✅ Rate limiting por IP (30 req/min) y usuario (100 req/min)
- ✅ Validación de entrada contra inyección de prompts
- ✅ Headers de seguridad (HSTS, CSP, X-Frame-Options)
- ✅ Detección de alucinaciones del LLM
- ✅ Logging estructurado de todas las operaciones

### Pendiente para Producción
- ⏳ Encriptación de datos sensibles en reposo
- ⏳ Auditoría completa de accesos
- ⏳ Rotación automática de secrets
- ⏳ WAF (Web Application Firewall)

## 📈 Métricas de Rendimiento

### Objetivos
- ⏱️ Tiempo de respuesta LLM: < 5 segundos (95th percentile)
- ✅ Tasa de éxito conversacional: > 90%
- 🎯 Precisión de validación: > 95%
- 🚀 Disponibilidad: > 99.9%

## 🤝 Contribución

### Guía de Contribución
1. Fork del repositorio
2. Crear branch feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit con mensajes descriptivos
4. Push al branch: `git push origin feature/nueva-funcionalidad`
5. Abrir Pull Request

### Estándares de Código
```bash
# Formateo
black backend/src backend/tests

# Linting
ruff check backend/src backend/tests

# Type checking (opcional)
mypy backend/src
```

## 📄 Licencia

MIT License - Ver archivo LICENSE

## 👥 Equipo

Desarrollado para la **Defensoría Civil de San Rafael, Mendoza, Argentina**

## 📞 Soporte

Para consultas técnicas o reportar issues:
- 📧 Email: soporte@defensoria-sr.gob.ar
- 🐛 Issues: GitHub Issues
- 📖 Documentación: `/docs` endpoint

---

**⚖️ Sistema de Defensoría Civil** - Automatizando la justicia con IA responsable
Test line
