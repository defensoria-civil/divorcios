# Análisis de Datos: Escritos Judiciales vs Sistema Actual

## Resumen Ejecutivo

✅ **Estado General:** Los datos recolectados cubren ~85% de lo requerido  
⚠️ **Campos Faltantes:** 6 campos críticos  
🔄 **Acción Requerida:** Extender flujo conversacional y modelo de datos

---

## Comparación Detallada por Sección

### 📋 SECCIÓN I: DATOS PERSONALES

#### DIVORCIO BILATERAL (ambos cónyuges)

| Campo Requerido | Campo en BD | Estado | Notas |
|----------------|-------------|--------|-------|
| Nombre completo persona 1 | `apellido`, `nombres` | ✅ | Implementado separado |
| DNI persona 1 | `dni` | ✅ | |
| Nacionalidad persona 1 | ❌ | ⚠️ FALTA | Asumir "argentino/a" o preguntar |
| Estado civil | ❌ | ⚠️ FALTA | Siempre "casado/a" al iniciar |
| Edad persona 1 | `fecha_nacimiento` | ✅ | Calcular desde fecha |
| Ocupación persona 1 | ❌ | ⚠️ FALTA | Ej: "desempleado", "ama de casa" |
| Domicilio real persona 1 | `domicilio` | ✅ | |
| Celular persona 1 | `phone` | ✅ | |
| Email persona 1 | ❌ | ⚠️ FALTA | Importante para notificaciones |
| Nombre completo persona 2 | `apellido_conyuge`, `nombres_conyuge` | ✅ | |
| DNI persona 2 | `dni_conyuge` | ✅ | |
| Nacionalidad persona 2 | ❌ | ⚠️ FALTA | |
| Edad persona 2 | ❌ | ⚠️ FALTA | Necesitamos `fecha_nacimiento_conyuge` |
| Ocupación persona 2 | ❌ | ⚠️ FALTA | |
| Domicilio persona 2 | ❌ | ⚠️ FALTA | Necesitamos `domicilio_conyuge` |
| Celular persona 2 | ❌ | ⚠️ FALTA | Necesitamos `phone_conyuge` |
| Email persona 2 | ❌ | ⚠️ FALTA | |

#### DIVORCIO UNILATERAL (solo peticionante)

| Campo Requerido | Campo en BD | Estado | Notas |
|----------------|-------------|--------|-------|
| Todos los datos persona 1 | Ver arriba | Parcial | Mismo análisis |
| Nombre completo cónyuge | `apellido_conyuge`, `nombres_conyuge` | ✅ | |
| DNI cónyuge | `dni_conyuge` | ✅ | |
| Domicilio cónyuge | ❌ | ⚠️ FALTA | Requerido para notificación |

---

### 📋 SECCIÓN II: DOMICILIO LEGAL

| Campo Requerido | Estado | Notas |
|----------------|--------|-------|
| Domicilio de la Defensoría | ✅ | **HARDCODED**: "E. Civit N° 257, San Rafael" |

**Acción:** Crear constante en configuración o base de datos para datos institucionales.

---

### 📋 SECCIÓN III: BENEFICIO DE LITIGAR SIN GASTOS

| Campo Requerido | Estado | Notas |
|----------------|--------|-------|
| Texto legal estándar | ✅ | Se incluye automáticamente |

---

### 📋 SECCIÓN IV: COMPETENCIA

| Campo Requerido | Campo en BD | Estado | Notas |
|----------------|-------------|--------|-------|
| Último domicilio conyugal | `domicilio` | ✅ | Se usa domicilio del peticionante |

**Nota:** En BILATERAL se usa el domicilio de ambos (debe coincidir). En UNILATERAL se usa el del peticionante.

---

### 📋 SECCIÓN V: OBJETO

| Campo Requerido | Estado | Notas |
|----------------|--------|-------|
| Tipo de divorcio | `type` | ✅ | "unilateral" o "conjunta" |
| Texto legal estándar | ✅ | Se genera automáticamente |

---

### 📋 SECCIÓN VI: HECHOS

| Campo Requerido | Campo en BD | Estado | Notas |
|----------------|-------------|--------|-------|
| Número de acta matrimonio | ❌ | ⚠️ FALTA | Extraer de OCR acta |
| Libro Registro | ❌ | ⚠️ FALTA | Extraer de OCR acta |
| Año del acta | ❌ | ⚠️ FALTA | Extraer de OCR acta |
| Foja | ❌ | ⚠️ FALTA | Extraer de OCR acta |
| Oficina registro civil | ❌ | ⚠️ FALTA | Extraer de OCR acta ("San Rafael") |
| Fecha de matrimonio | `fecha_matrimonio` | ✅ | |
| Lugar de matrimonio | `lugar_matrimonio` | ✅ | |
| Fecha de separación | ❌ | ⚠️ FALTA | Importante para cálculo de plazos |

**Acción Crítica:** El OCR del acta de matrimonio debe extraer:
- Número de acta
- Libro
- Año
- Foja
- Oficina

---

### 📋 SECCIÓN VII: PROPUESTA REGULADORA

#### A. Inmuebles y Bienes Registrables

| Campo Requerido | Campo en BD | Estado | Notas |
|----------------|-------------|--------|-------|
| ¿Tienen bienes inmuebles? | `tiene_bienes` | ✅ | Boolean |
| Detalle de bienes | `info_bienes` | ✅ | Texto libre |

**Estado:** ✅ Cubierto. El flujo pregunta si hay bienes y guarda la info.

#### B. Bienes Muebles y Útiles del Hogar

| Campo Requerido | Estado | Notas |
|----------------|--------|-------|
| Estado de reparto | ✅ | Se asume "repartidos al momento de separación" |

**Estado:** ✅ Cubierto con texto estándar.

#### C. Responsabilidad Parental (Hijos)

| Campo Requerido | Campo en BD | Estado | Notas |
|----------------|-------------|--------|-------|
| ¿Tienen hijos menores? | `tiene_hijos` | ✅ | Boolean |
| Datos de hijos menores | `info_hijos` | ✅ | Texto libre |

**Estado:** ✅ Cubierto. Si hay hijos, el sistema pide datos.

---

### 📋 SECCIÓN VIII: PRUEBA

| Campo Requerido | Estado | Notas |
|----------------|--------|-------|
| Acta de matrimonio | `marriage_cert_url` | ✅ | URL del documento |
| Copia DNI | `dni_image_url` | ✅ | URL del documento |

**Estado:** ✅ Los documentos se almacenan y pueden adjuntarse.

---

### 📋 SECCIÓN IX: DERECHO

| Campo Requerido | Estado | Notas |
|----------------|--------|-------|
| Citas legales estándar | ✅ | Texto fijo (Arts. 435, 437, 438 CCCN, etc.) |

---

### 📋 SECCIÓN X: PETITORIO

| Campo Requerido | Estado | Notas |
|----------------|--------|-------|
| Texto legal estándar | ✅ | Se genera según tipo de divorcio |

---

## 🚨 Campos Críticos Faltantes

### Alta Prioridad (Requeridos para escrito completo)

1. **Email del peticionante** (`email`)
2. **Fecha de separación** (`fecha_separacion`)
3. **Datos del acta de matrimonio** (5 campos):
   - `acta_numero`
   - `acta_libro`
   - `acta_anio`
   - `acta_foja`
   - `acta_oficina`

### Prioridad Media (Mejoran completitud)

4. **Ocupación del peticionante** (`ocupacion`)
5. **Domicilio del cónyuge** (`domicilio_conyuge`) - Solo para UNILATERAL
6. **Nacionalidad** (`nacionalidad`, `nacionalidad_conyuge`)

### Prioridad Baja (Pueden asumirse o calcular)

7. **Edad explícita** - Se calcula desde `fecha_nacimiento`
8. **Estado civil** - Siempre "casado/a" al iniciar trámite

---

## 📝 Plan de Acción

### 1. Extender Modelo de Datos

```python
# Agregar a models.py (Case)
email = Column(String(120), nullable=True)
ocupacion = Column(String(80), nullable=True)
nacionalidad = Column(String(32), default="argentino/a")
fecha_separacion = Column(Date, nullable=True)

# Datos del acta de matrimonio (extraer con OCR)
acta_numero = Column(String(16), nullable=True)
acta_libro = Column(String(32), nullable=True)
acta_anio = Column(String(8), nullable=True)
acta_foja = Column(String(16), nullable=True)
acta_oficina = Column(String(120), nullable=True)

# Datos del cónyuge (solo para bilateral o completitud)
domicilio_conyuge = Column(Text, nullable=True)
fecha_nacimiento_conyuge = Column(Date, nullable=True)
ocupacion_conyuge = Column(String(80), nullable=True)
nacionalidad_conyuge = Column(String(32), default="argentino/a")
phone_conyuge = Column(String(32), nullable=True)
email_conyuge = Column(String(120), nullable=True)
```

### 2. Extender Flujo Conversacional

Agregar fases al chatbot:
- `email` - "¿Cuál es tu email para notificaciones?"
- `ocupacion` - "¿Cuál es tu ocupación actual?"
- `fecha_separacion` - "¿Cuándo se separaron de hecho?"

Para **BILATERAL**, agregar:
- `email_conyuge`
- `domicilio_conyuge` (debe coincidir o especificar actual)
- `ocupacion_conyuge`

### 3. Mejorar OCR del Acta de Matrimonio

El servicio OCR debe extraer:
```python
{
    "acta_numero": "167",
    "acta_libro": "10297",
    "acta_anio": "2021",
    "acta_foja": "50",
    "acta_oficina": "San Rafael",
    "fecha_matrimonio": "2021-02-05",
    "lugar_matrimonio": "San Rafael, Mendoza"
}
```

### 4. Validaciones Pre-Generación

Antes de generar PDF, verificar:
- ✅ Datos personales completos (nombre, DNI, domicilio, email)
- ✅ Datos de matrimonio completos (fecha, lugar, acta)
- ✅ Datos del cónyuge (al menos nombre y DNI)
- ✅ Fecha de separación
- ✅ Propuesta reguladora (bienes, hijos)

---

## 📊 Cobertura Actual

| Sección | Cobertura | Campos Faltantes |
|---------|-----------|------------------|
| I. Datos Personales | 65% | 8 campos |
| II. Domicilio Legal | 100% | 0 |
| III. Beneficio | 100% | 0 |
| IV. Competencia | 100% | 0 |
| V. Objeto | 100% | 0 |
| VI. Hechos | 60% | 6 campos (acta) |
| VII. Propuesta Reguladora | 90% | 0 |
| VIII. Prueba | 100% | 0 |
| IX. Derecho | 100% | 0 |
| X. Petitorio | 100% | 0 |
| **TOTAL** | **85%** | **14 campos** |

---

## ✅ Recomendaciones

### Corto Plazo (Sprint Actual)
1. ✅ Agregar campo `email` al flujo conversacional
2. ✅ Agregar campo `fecha_separacion` al flujo
3. ✅ Mejorar OCR para extraer datos completos del acta

### Mediano Plazo
4. Agregar campos opcionales (ocupación, nacionalidad)
5. Para BILATERAL, extender flujo para recolectar datos del segundo cónyuge
6. Implementar validación de completitud antes de generar PDF

### Consideraciones
- Los campos de **nacionalidad** pueden asumir "argentino/a" por defecto
- La **edad** se calcula automáticamente desde `fecha_nacimiento`
- El **estado civil** es siempre "casado/a" al inicio del trámite
- Para **UNILATERAL**, solo se requieren datos básicos del cónyuge (nombre, DNI, domicilio para notificación)
