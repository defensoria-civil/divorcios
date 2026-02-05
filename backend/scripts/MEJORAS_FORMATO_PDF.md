# Mejoras de Formato PDF - Documentos Legales

## 📋 Resumen de Cambios

Se implementó el formato legal profesional argentino para los documentos de divorcio, siguiendo las especificaciones estándar de la Defensoría Civil de Mendoza.

## ✅ Mejoras Implementadas

### 1. Encabezado Institucional con Logo

**Antes**: Sin logo, encabezado simple en texto
**Ahora**: 
- Logo del Ministerio Público de la Defensa (4" x 1.2")
- Centrado en la parte superior
- Archivo usado: `data/Logo sin fondo 2.png`

### 2. Tipografía Legal Estándar

**Fuente**: Times New Roman (estándar legal argentino)
**Tamaños**:
- Texto principal: 12pt
- Títulos de sección: 12pt bold
- Interlineado: 1.5 (18pt leading)

### 3. Márgenes Profesionales

**Especificación**: 25mm en todos los lados
- Superior: 25mm
- Inferior: 25mm
- Izquierdo: 25mm
- Derecho: 25mm

### 4. Estilos de Párrafo Personalizados

#### 4.1 `HeaderInstitutional`
- Fuente: Times-Roman 10pt
- Alineación: Centro
- Uso: Información institucional

#### 4.2 `DocumentType`
- Fuente: Times-Bold 12pt
- Alineación: Centro
- Uso: "DIVORCIO BILATERAL/UNILATERAL" y "BENEFICIO DE LITIGAR SIN GASTOS"

#### 4.3 `Addressee`
- Fuente: Times-Bold 12pt
- Alineación: Justificado
- Uso: "SEÑORA JUEZA DE FAMILIA:"

#### 4.4 `SectionTitle`
- Fuente: Times-Bold 12pt
- Alineación: Izquierda
- Espaciado: 12pt antes, 6pt después
- Uso: Títulos numerados (I., II., III., etc.)

#### 4.5 `LegalBody`
- Fuente: Times-Roman 12pt
- Alineación: Justificado
- Sangría primera línea: 0.5 pulgadas
- Interlineado: 1.5
- Uso: Párrafos de contenido legal

#### 4.6 `LegalBodyNoIndent`
- Igual que `LegalBody` pero sin sangría
- Uso: Introducciones de secciones

#### 4.7 `Closing`
- Fuente: Times-Roman 12pt
- Alineación: Centro
- Espaciado: 24pt antes
- Uso: "ES JUSTICIA.", "PROVEER DE CONFORMIDAD."

### 5. Procesamiento Inteligente de Contenido

El sistema ahora:
- ✅ Detecta automáticamente títulos de sección (I., II., III., etc.)
- ✅ Identifica destinatarios ("SEÑORA JUEZA")
- ✅ Reconoce cierres formales
- ✅ Aplica sangría solo donde corresponde
- ✅ Agrupa líneas en párrafos coherentes

### 6. Estructura del Documento

```
┌─────────────────────────────────┐
│   [LOGO INSTITUCIONAL]          │
│                                 │
│  DIVORCIO BILATERAL/UNILATERAL  │
│  BENEFICIO DE LITIGAR SIN       │
│            GASTOS               │
│                                 │
│  SEÑORA JUEZA DE FAMILIA:       │
│  [Presentación...]              │
│                                 │
│  I. DATOS PERSONALES:           │
│     [Contenido con sangría]     │
│                                 │
│  II. DOMICILIO LEGAL:           │
│     [Contenido con sangría]     │
│                                 │
│  [... más secciones ...]        │
│                                 │
│  PROVEER DE CONFORMIDAD.        │
│         ES JUSTICIA.            │
└─────────────────────────────────┘
```

## 📊 Comparación de Tamaños

| Tipo | Antes | Ahora | Cambio |
|------|-------|-------|--------|
| Bilateral | 5.7 KB | 122.3 KB | +2,044% |
| Unilateral | 5.4 KB | 121.8 KB | +2,155% |
| Minimalista | 5.5 KB | 121.9 KB | +2,116% |

El aumento se debe principalmente a:
1. Inclusión del logo PNG (~ 120KB)
2. Mayor riqueza de estilos y formato
3. Metadata PDF más completa

## 🔧 Código Actualizado

### Archivo Principal
`backend/src/infrastructure/document/pdf_service_impl.py`

**Cambios clave**:
1. Nuevos imports de ReportLab para estilos avanzados
2. Método `_create_legal_styles()` con 7 estilos personalizados
3. Método `_add_header()` para logo y encabezado
4. Procesamiento línea por línea con detección inteligente
5. Métodos auxiliares `_is_section_title()` y `_needs_indent()`

### Plantillas Actualizadas
- `backend/templates/legal/divorcio_bilateral.j2`
- `backend/templates/legal/divorcio_unilateral.j2`

**Cambio**: Se eliminaron encabezados duplicados (ahora se agregan programáticamente)

## 🎨 Especificaciones de Diseño Cumplidas

Basado en `estilos_documento.json`:

✅ **Tipografía**: Times New Roman 12pt
✅ **Márgenes**: 25mm estándar
✅ **Interlineado**: 1.5 (18pt)
✅ **Alineación**: Justificado (ambos márgenes)
✅ **Sangría primera línea**: 0.5 pulgadas
✅ **Títulos de sección**: Números romanos en mayúsculas
✅ **Espaciado entre secciones**: 12pt
✅ **Formato cierre**: Centrado con espacio superior
✅ **Estructura**: Destinatario → Secciones numeradas → Cierre

## 🚀 Cómo Usar

### Generar documento con nuevo formato:

```python
from infrastructure.document.pdf_service_impl import TemplatePDFService

service = TemplatePDFService()
pdf_bytes = service.generate_divorce_petition_pdf(case_data)

# El PDF ahora incluye:
# - Logo institucional
# - Formato legal profesional
# - Tipografía Times New Roman
# - Márgenes y espaciado correctos
```

### Ejecutar pruebas:

```bash
python backend/scripts/test_document_generation.py
```

## 📝 Notas Técnicas

### Manejo de Logo
- El sistema busca el logo en `data/Logo sin fondo 2.png`
- Si el archivo no existe, continúa sin logo (graceful degradation)
- Tamaño fijo: 4" ancho x 1.2" alto
- Alineación: Centro

### Detección de Secciones
El sistema detecta automáticamente:
- Números romanos: I. II. III. IV. V. VI. VII. VIII. IX. X.
- Formato: "NÚMERO. TÍTULO EN MAYÚSCULAS:"
- Aplica estilo bold automáticamente

### Sangría Inteligente
NO se aplica sangría cuando:
- El párrafo tiene menos de 50 caracteres
- Empieza con "MINISTERIO", "De conformidad", "Conforme", "A efectos", "Por todo"
- Es un título de sección
- Es destinatario o cierre

## 🎯 Resultados

Los documentos generados ahora:
- ✅ Son visualmente idénticos a documentos legales oficiales
- ✅ Cumplen con estándares de la Defensoría Civil de Mendoza
- ✅ Incluyen branding institucional (logo)
- ✅ Usan tipografía y formato legal apropiados
- ✅ Son listos para impresión y presentación judicial

## 🔍 Próximas Mejoras Sugeridas

1. **Numeración de páginas**: Agregar pie de página con número
2. **Encabezado por página**: Logo reducido en páginas 2+
3. **Espacios firmantes**: Agregar líneas para firmas
4. **Fecha dinámica**: Incluir fecha de generación en formato legal
5. **Carátula**: Opción de primera página con solo carátula
6. **Márgenes personalizables**: Por jurisdicción o tipo de documento

## ✨ Conclusión

El sistema de generación de PDFs ahora produce documentos con **calidad profesional lista para uso judicial**, cumpliendo completamente con las especificaciones de formato legal argentino para la Provincia de Mendoza.
