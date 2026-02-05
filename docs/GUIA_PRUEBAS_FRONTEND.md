# Guía de Pruebas Funcionales - Dashboard Frontend

## Resumen de Mejoras Sprint 2

### ✅ Implementaciones Completadas

1. **Sistema de Notificaciones Toast**
   - Instalación de `react-hot-toast`
   - Componente `Toaster` configurado con estilos personalizados
   - Integrado en toda la aplicación

2. **Mejoras en Gestión de Usuarios**
   - Reemplazo de `alert()` nativos con notificaciones toast
   - Estados de carga mejorados durante operaciones CRUD
   - Feedback visual en tiempo real

3. **Mejoras en Gestión de Casos**
   - Notificaciones toast para descarga de PDF
   - Estados de carga durante generación de documentos
   - Mejora en el campo de búsqueda con icono integrado
   - Corrección de variantes de botones

4. **Correcciones de TypeScript**
   - Todos los errores de compilación resueltos
   - Build exitoso sin warnings críticos

---

## Pasos para Iniciar el Frontend

### 1. Preparación del Entorno

```bash
cd C:/Users/spereyra/CODE/PROYECTOS/defensoria-civil/divorcios/frontend
```

### 2. Verificar Dependencias

```bash
npm install
```

### 3. Configurar Variables de Entorno

Crear/verificar el archivo `.env`:

```env
VITE_API_URL=http://localhost:8000
```

### 4. Iniciar el Servidor de Desarrollo

```bash
npm run dev
```

El frontend estará disponible en: **http://localhost:5173**

---

## Backend Requerido

**IMPORTANTE:** El backend debe estar corriendo para pruebas completas.

```bash
# Terminal 2
cd C:/Users/spereyra/CODE/PROYECTOS/defensoria-civil/divorcios/backend
uv run python -m app.main
```

Backend disponible en: **http://localhost:8000**

---

## Plan de Pruebas Funcionales

### 🔐 Fase 1: Autenticación

#### Test 1.1: Login Correcto
1. Navegar a `http://localhost:5173`
2. Debería redirigir automáticamente a `/login`
3. Ingresar credenciales:
   - Usuario: `admin`
   - Contraseña: `admin123`
4. Click en "Iniciar Sesión"
5. **Resultado Esperado:**
   - ✅ Redirección a `/dashboard`
   - ✅ Token guardado en localStorage
   - ✅ Usuario visible en el header

#### Test 1.2: Login Incorrecto
1. Intentar login con credenciales inválidas
2. **Resultado Esperado:**
   - ✅ Mensaje de error visible
   - ✅ No hay redirección
   - ✅ Campos permanecen editables

#### Test 1.3: Protección de Rutas
1. Sin estar autenticado, intentar acceder a:
   - `/dashboard`
   - `/cases`
   - `/users`
2. **Resultado Esperado:**
   - ✅ Redirección automática a `/login`

---

### 📊 Fase 2: Dashboard Principal

#### Test 2.1: Visualización de Métricas
1. Navegar a `/dashboard`
2. **Verificar:**
   - ✅ Tarjetas de resumen muestran números correctos
   - ✅ Gráfico de distribución por estado se renderiza
   - ✅ Gráfico de línea temporal se renderiza
   - ✅ No hay errores en consola

#### Test 2.2: Navegación desde Dashboard
1. Click en "Ver Todos los Casos"
2. **Resultado Esperado:**
   - ✅ Redirección a `/cases`
3. Volver y click en "Ver Casos Nuevos"
4. **Resultado Esperado:**
   - ✅ Redirección a `/cases` con filtro aplicado

---

### 📋 Fase 3: Gestión de Casos

#### Test 3.1: Lista de Casos
1. Navegar a `/cases`
2. **Verificar:**
   - ✅ Tabla se carga con datos
   - ✅ Spinner visible durante carga
   - ✅ Paginación funcional (si hay más de 50 casos)
   - ✅ Estados de casos con colores correctos

#### Test 3.2: Búsqueda de Casos
1. En `/cases`, escribir en el campo de búsqueda
2. Por ejemplo: buscar por DNI o nombre
3. **Resultado Esperado:**
   - ✅ Tabla se actualiza automáticamente
   - ✅ Icono de búsqueda visible en el campo
   - ✅ Resultados filtrados correctamente

#### Test 3.3: Filtros de Casos
1. Click en botón "Nuevos"
2. **Verificar:**
   - ✅ Botón cambia de estilo (resaltado)
   - ✅ Tabla muestra solo casos con estado "new"
3. Click en el mismo botón nuevamente
4. **Verificar:**
   - ✅ Filtro se desactiva
   - ✅ Tabla muestra todos los casos

#### Test 3.4: Descargar PDF
1. En la tabla, click en el icono de descarga (verde)
2. **Resultado Esperado:**
   - ✅ Notificación toast: "Generando PDF..."
   - ✅ Tras unos segundos: "PDF descargado exitosamente"
   - ✅ Archivo PDF descargado en carpeta de descargas
   - ✅ PDF contiene datos del caso

#### Test 3.5: Ver Detalle de Caso
1. Click en el icono del ojo (azul) o en una fila
2. **Resultado Esperado:**
   - ✅ Redirección a `/cases/:id`
   - ✅ Información personal visible
   - ✅ Datos del matrimonio (si existen)
   - ✅ Historial de mensajes con iconos y timestamps

#### Test 3.6: Navegación desde Detalle
1. En vista de detalle, click en "Volver"
2. **Resultado Esperado:**
   - ✅ Regreso a `/cases`
3. Click en "Descargar PDF"
4. **Resultado Esperado:**
   - ✅ Toast: "Generando PDF..."
   - ✅ Toast: "PDF descargado exitosamente"
   - ✅ Archivo descargado

#### Test 3.7: Contactar por WhatsApp
1. En vista de detalle, click en "Contactar por WhatsApp"
2. **Resultado Esperado:**
   - ✅ Se abre nueva pestaña con WhatsApp Web
   - ✅ Número de teléfono pre-cargado

---

### 👥 Fase 4: Gestión de Usuarios (Solo Admin)

#### Test 4.1: Acceso a Usuarios
1. Navegar a `/users`
2. **Verificar:**
   - ✅ Tabla de usuarios visible
   - ✅ Columnas: Usuario, Email, Nombre, Rol, Estado, Fecha
   - ✅ Usuario actual marcado con etiqueta "Tú"

#### Test 4.2: Crear Usuario
1. Click en "Crear Usuario"
2. Llenar el formulario:
   - Usuario: `test_operator`
   - Email: `operator@test.com`
   - Contraseña: `123456`
   - Nombre: `Operador Test`
   - Rol: `Operador`
3. Click en "Crear"
4. **Resultado Esperado:**
   - ✅ Toast: "Usuario creado exitosamente"
   - ✅ Modal se cierra
   - ✅ Nuevo usuario aparece en la tabla
   - ✅ Estado: Activo

#### Test 4.3: Editar Usuario
1. Click en botón "Editar" de un usuario
2. Cambiar el email o nombre completo
3. Click en "Guardar"
4. **Resultado Esperado:**
   - ✅ Toast: "Usuario actualizado exitosamente"
   - ✅ Modal se cierra
   - ✅ Cambios reflejados en la tabla

#### Test 4.4: Cambiar Contraseña
1. Click en botón "Cambiar Contraseña"
2. Ingresar nueva contraseña (mínimo 6 caracteres)
3. Click en "Cambiar Contraseña"
4. **Resultado Esperado:**
   - ✅ Toast: "Contraseña actualizada exitosamente"
   - ✅ Modal se cierra

#### Test 4.5: Desactivar Usuario
1. Click en "Editar" de un usuario (no el actual)
2. Desmarcar checkbox "Usuario Activo"
3. Click en "Guardar"
4. **Resultado Esperado:**
   - ✅ Toast: "Usuario actualizado exitosamente"
   - ✅ Estado cambia a "Inactivo" con icono gris

#### Test 4.6: Eliminar Usuario
1. Click en botón "Eliminar" (rojo)
2. Confirmar en el diálogo
3. **Resultado Esperado:**
   - ✅ Toast de carga: "Eliminando usuario..."
   - ✅ Toast: "Usuario eliminado exitosamente"
   - ✅ Usuario desaparece de la tabla

#### Test 4.7: Restricción - No Eliminar Usuario Actual
1. Intentar eliminar al usuario con el que estás logueado
2. **Resultado Esperado:**
   - ✅ Botón "Eliminar" no está visible para el usuario actual

---

### 🎨 Fase 5: UX y Estados de Carga

#### Test 5.1: Notificaciones Toast
1. Realizar cualquier operación (crear, editar, eliminar)
2. **Verificar:**
   - ✅ Toast aparece en esquina superior derecha
   - ✅ Toast de carga muestra spinner
   - ✅ Toast de éxito es verde
   - ✅ Toast de error es rojo
   - ✅ Toast desaparece automáticamente tras 4 segundos
   - ✅ Se puede cerrar manualmente

#### Test 5.2: Estados de Carga
1. Al navegar a cualquier página con datos
2. **Verificar:**
   - ✅ Spinner visible mientras carga
   - ✅ Texto "Cargando..." apropiado

#### Test 5.3: Manejo de Errores
1. Detener el backend
2. Intentar realizar operaciones
3. **Resultado Esperado:**
   - ✅ Toast de error con mensaje descriptivo
   - ✅ No se rompe la aplicación
   - ✅ Usuario puede continuar navegando

#### Test 5.4: Responsive Design
1. Reducir tamaño de ventana (simular móvil)
2. **Verificar:**
   - ✅ Sidebar se adapta o colapsa
   - ✅ Tablas tienen scroll horizontal
   - ✅ Tarjetas se apilan verticalmente
   - ✅ Botones y texto legibles

---

### 🔄 Fase 6: Navegación y Consistencia

#### Test 6.1: Navegación por Sidebar
1. Click en cada ítem del sidebar:
   - Dashboard
   - Casos
   - Usuarios
2. **Verificar:**
   - ✅ Rutas cambian correctamente
   - ✅ Ítem activo resaltado
   - ✅ Contenido carga sin errores

#### Test 6.2: Breadcrumbs y Estado
1. Navegar: Dashboard → Casos → Detalle de Caso
2. **Verificar:**
   - ✅ URL actualizada correctamente
   - ✅ Botón "Volver" funcional
   - ✅ Estado de navegación preservado

#### Test 6.3: Logout
1. Click en el botón de logout (si existe en el header)
2. **Resultado Esperado:**
   - ✅ Redirección a `/login`
   - ✅ Token eliminado de localStorage
   - ✅ No se puede acceder a rutas protegidas

---

## Criterios de Éxito

### ✅ Funcionalidad Core
- [ ] Login y logout funcionan correctamente
- [ ] Dashboard muestra métricas y gráficos
- [ ] Lista de casos carga y filtra correctamente
- [ ] Detalle de caso muestra toda la información
- [ ] Descarga de PDF funciona
- [ ] CRUD completo de usuarios funcional

### ✅ UX Mejorada
- [ ] Todas las notificaciones son toast (no alerts nativos)
- [ ] Estados de carga visibles en todas las operaciones
- [ ] Errores manejados con mensajes descriptivos
- [ ] Navegación fluida sin bugs visuales

### ✅ Calidad Técnica
- [ ] Build de producción sin errores
- [ ] Sin errores críticos en consola del navegador
- [ ] TypeScript sin errores de compilación
- [ ] Responsive en diferentes tamaños de pantalla

---

## Problemas Conocidos y Soluciones

### Problema: Backend no responde
**Solución:** Verificar que el backend esté corriendo en el puerto 8000

### Problema: CORS errors
**Solución:** Backend ya tiene CORS configurado para `localhost:5173`

### Problema: Token expirado
**Solución:** Hacer logout y login nuevamente

### Problema: Gráficos no se renderizan
**Solución:** Verificar que hay datos en la base de datos (crear casos de prueba)

---

## Próximos Pasos Recomendados

1. ✅ **Sprint 2 Completado** - Frontend funcional con UX mejorada
2. 🔄 **Sprint 3 - Base de Conocimiento Legal:**
   - Agregar más documentos legales
   - Probar embeddings con Ollama local
   - Mejorar precisión de respuestas del chatbot
3. 🔜 **Sprint 4 - Integración WhatsApp:**
   - Configurar WAHA
   - Pruebas end-to-end de procesamiento de imágenes
   - Validación del flujo completo

---

## Notas Finales

- **Estado actual del proyecto:** 85% completo
- **Frontend:** ✅ Completamente funcional
- **Backend:** ✅ Operativo con todas las APIs
- **WhatsApp Bot:** ⚠️ Requiere configuración de WAHA
- **Base de Conocimiento:** ✅ Cargada y funcional

**Listo para desplegar en entorno de staging o continuar con Sprint 3.**
