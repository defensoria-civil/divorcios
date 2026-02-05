# 🔄 Análisis de la Máquina de Estados (Chatbot Flow)

Este documento detalla el funcionamiento de la máquina de estados finita que controla el flujo conversacional del chatbot de Defensoría Civil.

**Archivo Core:** `backend/src/application/use_cases/process_incoming_message.py`

---

## 1. Visión General

El sistema utiliza una máquina de estados explícita para guiar al usuario a través de un proceso lineal pero flexible de recolección de datos. Cada mensaje del usuario se procesa según el estado (`phase`) actual del caso.

**Características Clave:**
*   **Persistencia:** El estado se guarda en la base de datos (`cases.phase`).
*   **Validación Bloqueante:** No se avanza de estado hasta que el dato ingresado sea válido.
*   **Memoria de Sesión:** Datos complejos (como la lista de hijos) se gestionan con variables auxiliares en la `MemoryService`.
*   **Ramas Condicionales:** El flujo se bifurca según respuestas (ej: tiene hijos vs no tiene, trabaja vs desempleado).

---

## 2. Diagrama de Flujo (Macro)

1.  **Datos Personales Solicitante** (`inicio` → `domicilio`)
2.  **Perfil Económico (BLSG)** (`econ_intro` → `econ_cierre`)
3.  **Datos Cónyuge** (`apellido_conyuge` → `domicilio_conyuge`)
4.  **Datos Matrimonio** (`info_matrimonio` → `ultimo_domicilio_conyugal`)
5.  **Hijos (Loop)** (`hijos` → `hijos_cuantos` ↔ `hijo_eval`)
6.  **Bienes** (`bienes`)
7.  **Documentación** (`documentacion`)

---

## 3. Detalle de Estados y Transiciones

### 👤 Fase 1: Datos Personales

| Estado Actual | Input Esperado | Validación / Lógica | Estado Siguiente |
| :--- | :--- | :--- | :--- |
| `inicio` | (Cualquier texto) | Saludo inicial. | `tipo_divorcio` |
| `tipo_divorcio` | "unilateral" / "conjunta" | Detecta keywords. | `apellido` |
| `apellido` | Apellido | Longitud > 1. Convierte a MAYÚSCULAS. | `nombres` |
| `nombres` | Nombres | Longitud > 1. Capitaliza (Title Case). | `cuit` |
| `cuit` | CUIT/CUIL | Regex 11 dígitos. Extrae DNI automáticamente. | `fecha_nacimiento` |
| `fecha_nacimiento`| Fecha (DD/MM/AAAA) | Valida formato y fecha lógica. | `domicilio` |
| `domicilio` | Dirección | Valida calle, número, localidad (heurística). | `econ_intro` |

### 💰 Fase 2: Perfil Económico (Declaración Jurada)

| Estado Actual | Input Esperado | Validación / Lógica | Estado Siguiente |
| :--- | :--- | :--- | :--- |
| `econ_intro` | (Cualquier texto) | Intro informativa. Pasa directo. | `econ_situacion` |
| `econ_situacion` | Situación laboral | Mapea keywords (desocupado, dependencia, etc). | `econ_ingreso` (si trabaja) o `econ_vivienda` |
| `econ_ingreso` | Monto ($) | Extrae números. | `econ_vivienda` |
| `econ_vivienda` | Tipo vivienda | Keywords (alquila, propia, prestada). | `econ_alquiler` (si alquila) o `econ_patrimonio_inmuebles` |
| `econ_alquiler` | Monto ($) | Extrae números. | `econ_patrimonio_inmuebles` |
| `econ_patrimonio_inmuebles` | Texto / "No" | Guarda texto libre. | `econ_patrimonio_registrables` |
| `econ_patrimonio_registrables`| Texto / "No" | Guarda texto libre. | `econ_cierre` |
| `econ_cierre` | (Automático) | Calcula elegibilidad preliminar BLSG. | `apellido_conyuge` |

### 👥 Fase 3: Datos Cónyuge

| Estado Actual | Input Esperado | Validación / Lógica | Estado Siguiente |
| :--- | :--- | :--- | :--- |
| `apellido_conyuge`| Apellido | Longitud > 1. MAYÚSCULAS. | `nombres_conyuge` |
| `nombres_conyuge` | Nombres | Longitud > 1. Title Case. | `doc_conyuge` |
| `doc_conyuge` | DNI o CUIT | Regex 7-8 (DNI) o 11 (CUIT). | `fecha_nacimiento_conyuge` |
| `fecha_nacimiento_conyuge`| Fecha | Valida formato. | `domicilio_conyuge` |
| `domicilio_conyuge`| Dirección | Valida dirección completa. | `info_matrimonio` |

### 💍 Fase 4: Matrimonio

| Estado Actual | Input Esperado | Validación / Lógica | Estado Siguiente |
| :--- | :--- | :--- | :--- |
| `info_matrimonio` | Fecha y Lugar | Regex complejo para extraer fecha y lugar en lenguaje natural. | `ultimo_domicilio_conyugal` |
| `ultimo_domicilio_conyugal`| Dirección | Valida dirección (determina competencia judicial). | `hijos` |

### 👶 Fase 5: Hijos (Lógica de Loop)

| Estado Actual | Input Esperado | Validación / Lógica | Estado Siguiente |
| :--- | :--- | :--- | :--- |
| `hijos` | Sí/No | Si "No" → salta a `bienes`. | `hijos_cuantos` o `bienes` |
| `hijos_cuantos` | Número (N) | Guarda N en sesión. Inicializa índice i=0. | `hijo_nombre` |
| `hijo_nombre` | Nombre | Guarda nombre temporal. | `hijo_fecha` |
| `hijo_fecha` | Fecha Nac. | Calcula edad. <br>Si < 18: Incluye automático.<br>Si >= 18: Pide más info. | `hijo_mayor_eval` (si >= 18) o Loop/Fin |
| `hijo_mayor_eval` | CUD/Estudia/No | Decide inclusión según reglas (18-25 + estudia o CUD). | Loop (si i < N) o `bienes` |

### 🏠 Fase 6: Bienes y Cierre

| Estado Actual | Input Esperado | Validación / Lógica | Estado Siguiente |
| :--- | :--- | :--- | :--- |
| `bienes` | Texto / "No" | Guarda declaración de bienes. Genera resumen final. | `documentacion` |
| `documentacion` | Fotos / "Listo" | **Estado Final**. <br>- Acepta imágenes (DNI, Acta).<br>- Procesa OCR.<br>- Responde status de documentos pendientes. | (Se mantiene en `documentacion`) |

---

## 4. Mecanismos Especiales

### 🔄 Fallback a LLM
Si el mensaje del usuario no cumple con la validación de la fase actual (ej: se espera una fecha y envía una pregunta), el sistema invoca `_llm_fallback`.
*   El LLM recibe el contexto pero **NO cambia el estado**.
*   Responde la duda del usuario y el sistema vuelve a esperar el input correcto en el siguiente turno.

### 📸 Procesamiento de Imágenes (`_handle_media`)
Este método intercepta el flujo antes de la máquina de estados si el mensaje contiene una imagen.
*   Solo activo en fase `documentacion` (y parcialmente en `dni` si se implementara).
*   Detecta tipo de documento (DNI, Acta, ANSES) usando OCR.
*   Actualiza campos del caso (`dni_image_url`, `marriage_cert_url`) sin cambiar necesariamente de fase, salvo lógica específica.

### 🧠 Memoria de Sesión en Loops
Para el loop de hijos, que requiere iterar N veces, se usa `MemoryService` para persistir:
*   `hijos_total`: Cantidad total declarada.
*   `hijos_index`: Índice actual (0 a N-1).
*   `hijo_actual_*`: Datos temporales del hijo en proceso.
Esto permite que el loop sobreviva a reinicios del servidor o sesiones largas, ya que el estado se reconstruye desde la DB.
