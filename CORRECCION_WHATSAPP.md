# 📞 Corrección de Números de WhatsApp

## 🎯 Problema Identificado

Los números de WhatsApp se estaban guardando con el sufijo `@lid` o `@c.us` completo en la base de datos (ej: `261082623000696@lid`), lo que causaba:

1. ❌ Enlaces de WhatsApp inválidos (wa.me no reconoce el formato con @lid)
2. ❌ Error: "El número de teléfono +261 082623000696 no existe en WhatsApp"
3. ❌ Visualización confusa para los operadores

## ✅ Solución Implementada

### **Backend - Nuevos Archivos Creados:**

#### 1. **Utilidad de normalización de teléfonos**
`backend/src/infrastructure/utils/phone_utils.py`

Funciones implementadas:
- `normalize_whatsapp_phone()` - Limpia el número (remueve @lid, @c.us)
- `format_phone_for_display()` - Formatea para UI
- `format_phone_for_whatsapp()` - Formatea para enlaces wa.me
- `validate_phone_number()` - Valida números
- `extract_country_code()` - Extrae código de país

#### 2. **Script de migración**
`backend/scripts/migrate_phone_numbers.py`

Script para actualizar números existentes en la base de datos.

### **Cambios en Backend:**

#### `presentation/api/routes/webhook.py`
```python
# ANTES:
phone = msg.from_ or msg.chatId or "unknown"

# DESPUÉS:
phone_raw = msg.from_ or msg.chatId or "unknown"
phone = normalize_whatsapp_phone(phone_raw)  # Guarda limpio en DB

# Para enviar mensajes, usa phone_raw (con @lid)
await whatsapp.send_message(phone_raw, response.text)
```

**Lógica:**
- **Guardar en DB:** Número limpio sin @lid (`261082623000696`)
- **Enviar WhatsApp:** Número original con @lid (`261082623000696@lid`)

### **Mejoras en Frontend:**

#### Funcionalidades añadidas en CaseDetail.tsx:

1. **Formateo de número para visualización**
2. **Botón para copiar número**
3. **Enlace de WhatsApp mejorado**
4. **Mensaje pre-escrito personalizado**
5. **Logs de debugging en consola**

## 🚀 Pasos para Aplicar la Corrección

### **Paso 1: Verificar el Script (Dry Run)**

```bash
cd backend
python scripts/migrate_phone_numbers.py
```

Esto mostrará:
- Cuántos registros se actualizarían
- Qué cambios se harían
- Sin modificar la base de datos

### **Paso 2: Aplicar la Migración**

```bash
python scripts/migrate_phone_numbers.py --apply
```

Cuando pregunte, escribe `SI` para confirmar.

### **Paso 3: Reiniciar Backend**

```bash
# Si está corriendo con Docker
docker-compose restart backend

# Si está corriendo directamente
# Ctrl+C y volver a iniciar
uvicorn presentation.api.main:app --reload
```

### **Paso 4: Rebuild Frontend**

```bash
cd frontend
npm run build
```

### **Paso 5: Verificar**

1. Crear un nuevo caso de prueba por WhatsApp
2. Verificar en la base de datos que el número se guarda sin @lid
3. Probar el botón "Contactar por WhatsApp" en el dashboard
4. Verificar que el enlace funcione correctamente

## 📊 Ejemplo de Migración

### Antes:
```
cases.phone = "261082623000696@lid"
```

### Después:
```
cases.phone = "261082623000696"
```

## 🔍 Debugging

Si el botón de WhatsApp sigue sin funcionar:

1. **Abrir consola del navegador (F12)**
2. **Hacer clic en "Contactar por WhatsApp"**
3. **Revisar los logs:**
   ```
   Opening WhatsApp with: https://wa.me/261082623000696?text=...
   Phone number extracted: 261082623000696
   Original phone field: 261082623000696
   ```

4. **Verificar:**
   - ✅ URL no debe contener @lid
   - ✅ Número debe tener formato válido
   - ✅ Campo original debe estar limpio

## 🎨 Mejoras de UI Implementadas

### Vista del Teléfono:
```
Antes: 261082623000696@lid
Después: +26 108 2623000696 [📋]
         └─ Botón copiar
```

### Card de Acciones:
```
[📥 Descargar Demanda]
[📞 Contactar por WhatsApp]
    Número: 261082623000696
```

## ⚠️ Notas Importantes

### **Números que no funcionarán:**

El número `261082623000696` tiene **15 dígitos**, lo cual es inusual. Podría ser:

1. **Código de país incorrecto:**
   - Si es Argentina: debería ser `54` + área `261` + número
   - Formato correcto argentino: `5492611234567` (13 dígitos)

2. **Número no registrado en WhatsApp:**
   - El usuario podría no tener WhatsApp instalado
   - El número podría ser inválido

3. **Solución alternativa:**
   - Usar el botón de copiar [📋]
   - Buscar manualmente en WhatsApp
   - Contactar por otro medio

### **Para números argentinos válidos:**

Formato esperado: `549261XXXXXXX`
- `54` = Argentina
- `9` = Móvil
- `261` = Mendoza
- `XXXXXXX` = Número local

## 🧪 Testing

### **Test Manual:**

```bash
# En Python shell
from infrastructure.utils.phone_utils import normalize_whatsapp_phone

# Test 1: Número con @lid
assert normalize_whatsapp_phone("261082623000696@lid") == "261082623000696"

# Test 2: Número con @c.us
assert normalize_whatsapp_phone("5492611234567@c.us") == "5492611234567"

# Test 3: Número sin sufijo
assert normalize_whatsapp_phone("5492611234567") == "5492611234567"
```

## 📝 Checklist de Implementación

- [ ] Copiar archivos nuevos al backend
- [ ] Ejecutar migración en dry-run
- [ ] Aplicar migración con --apply
- [ ] Reiniciar backend
- [ ] Rebuild frontend
- [ ] Probar con caso existente
- [ ] Crear caso nuevo de prueba
- [ ] Verificar botón WhatsApp funciona
- [ ] Verificar logs en consola
- [ ] Documentar cualquier número problemático

## 🎯 Resultado Esperado

✅ **Números limpios en DB:** `261082623000696`  
✅ **Enlaces válidos:** `https://wa.me/261082623000696`  
✅ **Visualización clara:** `+26 108 2623000696`  
✅ **Funcionalidad completa:** Copiar, abrir WhatsApp, mensaje pre-escrito  

---

**Última actualización:** 06/11/2025  
**Status:** ✅ Ready to Deploy
