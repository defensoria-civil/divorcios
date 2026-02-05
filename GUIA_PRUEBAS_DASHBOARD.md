# 🧪 Guía de Pruebas - Dashboard Frontend

## Objetivo
Verificar que el Dashboard frontend se integre correctamente con el API backend y muestre datos reales.

---

## Pre-requisitos ✅

### Backend
- ✅ API corriendo en `http://localhost:8000`
- ✅ Base de datos con datos de prueba (5 casos, 2 usuarios)
- ✅ CORS configurado para `localhost:5173` y `localhost:5174`

### Frontend  
- ⏳ Frontend debe estar corriendo (puerto 5173 o 5174)
- ⏳ Archivo `.env` configurado con `VITE_API_URL=http://localhost:8000`

---

## Paso 1: Iniciar Frontend

### Opción A: Usar proceso existente
Si ya hay un proceso Node corriendo en puerto 5173 o 5174:
```bash
# Verificar en navegador
http://localhost:5173
# o
http://localhost:5174
```

### Opción B: Iniciar nuevo proceso
```bash
cd frontend
npm run dev
```

**Resultado esperado:**
```
VITE v5.4.21  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

---

## Paso 2: Probar Login

1. **Abrir navegador:** `http://localhost:5173/login` (o 5174)

2. **Credenciales de prueba:**
   - Usuario: `semper`
   - Password: `password123`
   
   **O:**
   - Usuario: `admin`
   - Password: `changeme123`

3. **Acciones:**
   - ✅ Ingresar credenciales
   - ✅ Click en "Iniciar Sesión"
   
4. **Resultado esperado:**
   - ✅ Redirect a `/` (Dashboard)
   - ✅ Token guardado en `localStorage`
   - ✅ Sin errores en consola del navegador

5. **Verificar en DevTools (F12):**
   ```javascript
   // En Console
   localStorage.getItem('access_token')
   // Debe mostrar: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   
   localStorage.getItem('user')
   // Debe mostrar JSON del usuario
   ```

---

## Paso 3: Verificar Dashboard

### 3.1 Tarjetas de Resumen

**Verificar que se muestren:**

1. **Casos Totales**
   - ✅ Debe mostrar: `5`
   - ✅ Texto: "X nuevos esta semana"

2. **Últimos 7 Días**
   - ✅ Debe mostrar: `0` (los casos de prueba son más antiguos)

3. **Últimos 30 Días**
   - ✅ Debe mostrar: `5`

4. **Completados**
   - ✅ Debe mostrar: `1` (caso con `status: completed`)

### 3.2 Gráfico de Distribución por Estado

**Verificar:**
- ✅ Gráfico de torta (pie chart) visible
- ✅ Debe mostrar segmentos para:
  - Nuevos: 3 casos
  - En espera de documentos: 1 caso
  - Completados: 1 caso
- ✅ Leyenda con porcentajes

### 3.3 Gráfico de Timeline

**Verificar:**
- ✅ Gráfico de línea visible
- ✅ Eje X: Fechas de los últimos 30 días
- ✅ Eje Y: Cantidad de casos
- ✅ Puntos en las fechas donde se crearon casos

### 3.4 Acciones Rápidas

**Verificar botones:**
- ✅ "Ver Todos los Casos"
- ✅ "Ver Casos Nuevos"
- ✅ "Ver Casos Completados"

---

## Paso 4: Verificar Navegación a Casos

1. **Click en "Ver Todos los Casos"**

2. **Resultado esperado:**
   - ✅ Redirect a `/cases`
   - ✅ Tabla con lista de 5 casos
   - ✅ Columnas: Teléfono, Nombre, DNI, Tipo, Estado, Fecha
   - ✅ Datos correctos según BD

3. **Verificar datos de ejemplo:**
   ```
   Juan Pérez - DNI 30123456 - Unilateral - Nuevo
   María González - DNI 28456789 - Conjunta - Nuevo
   Carlos López - DNI 32789012 - Unilateral - Nuevo
   Ana Martínez - DNI 29345678 - Conjunta - Completado
   Roberto Fernández - DNI 31234567 - Unilateral - Esperando docs
   ```

---

## Paso 5: Verificar Detalle de Caso

1. **Click en cualquier fila de la tabla de casos**

2. **Resultado esperado:**
   - ✅ Redirect a `/cases/:id` (ej: `/cases/1`)
   - ✅ Página de detalle con información del caso
   - ✅ Secciones:
     - Información Personal
     - Datos del Divorcio
     - Estado del Caso
     - Historial de Mensajes (si hay)

---

## Paso 6: Verificar Requests del API

**Abrir DevTools → Network Tab**

### Requests esperados al cargar Dashboard:

1. **GET `/api/metrics/summary`**
   - Status: `200 OK`
   - Response:
     ```json
     {
       "total_cases": 5,
       "recent_cases_7d": 0,
       "recent_cases_30d": 5,
       "by_status": {
         "new": 3,
         "waiting_documents": 1,
         "completed": 1
       },
       "by_type": {
         "unilateral": 3,
         "conjunta": 2
       }
     }
     ```

2. **GET `/api/metrics/by_status`**
   - Status: `200 OK`
   - Response:
     ```json
     [
       {"status": "new", "count": 3, "percent": 0.6},
       {"status": "waiting_documents", "count": 1, "percent": 0.2},
       {"status": "completed", "count": 1, "percent": 0.2}
     ]
     ```

3. **GET `/api/metrics/timeline?days=30`**
   - Status: `200 OK`
   - Response: Array con fechas y conteos

### Requests esperados al navegar a Casos:

4. **GET `/api/cases/?skip=0&limit=50`**
   - Status: `200 OK`
   - Response:
     ```json
     {
       "items": [...], // 5 casos
       "total": 5,
       "page": 1,
       "page_size": 50,
       "pages": 1
     }
     ```

---

## Paso 7: Verificar Auto-refresh

El Dashboard tiene auto-refresh cada 30 segundos.

**Verificar:**
1. ✅ Dejar el Dashboard abierto por 35 segundos
2. ✅ En Network tab, deben aparecer nuevos requests a `/api/metrics/*`
3. ✅ Los datos deben actualizarse automáticamente

---

## Paso 8: Verificar Logout

1. **Click en botón de Logout (si existe en la UI)**
   
   **O manualmente:**
   ```javascript
   // En Console del navegador
   localStorage.clear();
   window.location.reload();
   ```

2. **Resultado esperado:**
   - ✅ Redirect a `/login`
   - ✅ Token eliminado de localStorage
   - ✅ No se puede acceder a rutas protegidas sin login

---

## Checklist de Verificación ✅

### Funcionalidad del Dashboard
- [ ] Login funciona correctamente
- [ ] Métricas se cargan y muestran datos reales
- [ ] Tarjetas de resumen muestran números correctos
- [ ] Gráfico de distribución por estado se visualiza
- [ ] Gráfico de timeline se visualiza
- [ ] Auto-refresh funciona cada 30 segundos
- [ ] Botones de acciones rápidas funcionan

### Navegación
- [ ] "Ver Todos los Casos" navega a `/cases`
- [ ] Lista de casos muestra los 5 casos de prueba
- [ ] Click en caso navega a detalle `/cases/:id`
- [ ] Detalle de caso muestra información correcta

### API Integration
- [ ] Requests a `/api/metrics/*` retornan 200 OK
- [ ] Requests a `/api/cases/*` retornan 200 OK
- [ ] Token JWT se incluye en headers de requests
- [ ] CORS no genera errores

### UX/UI
- [ ] Loading spinners se muestran mientras carga
- [ ] No hay errores en consola del navegador
- [ ] Diseño responsive funciona en mobile/desktop
- [ ] Colores y tema se ven correctamente

---

## Problemas Comunes y Soluciones

### ❌ Error: "Network Error" o CORS
**Solución:**
```bash
# Verificar que API esté corriendo
curl http://localhost:8000/api/metrics/summary -H "Authorization: Bearer <TOKEN>"

# Verificar CORS en backend
# En backend/src/presentation/api/main.py debe tener:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### ❌ Error: "401 Unauthorized"
**Solución:**
```bash
# Hacer login nuevamente
# Verificar que token esté en localStorage
localStorage.getItem('access_token')

# Si no hay token o está expirado, logout y login de nuevo
```

### ❌ Dashboard no muestra datos
**Solución:**
1. Abrir DevTools → Network
2. Verificar que requests a `/api/metrics/*` retornen 200
3. Si retornan 403, verificar autenticación
4. Si retornan 500, verificar logs del backend:
   ```bash
   docker logs divorcios-api-1 --tail 50
   ```

### ❌ Frontend no carga
**Solución:**
```bash
cd frontend
npm install
npm run dev
```

---

## Resultado Esperado Final

✅ **Dashboard completamente funcional** mostrando:
- Métricas reales desde la BD
- Gráficos interactivos
- Navegación fluida entre páginas
- Auto-refresh funcionando
- Sin errores en consola

---

## Próximo Paso

Una vez verificado el Dashboard, proceder con:
- **Paso 3: Tests de Integración** (crear tests automatizados)
- **Paso 1: Prueba de Procesamiento de Imágenes** (requiere configurar WAHA)

---

**Fecha:** 31 de Octubre 2025  
**Prioridad:** ALTA 🔴
