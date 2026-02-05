# Mejoras para Impresión a Doble Cara

## 📋 Cambios Implementados

### 1. Logo Más Grande y Visible

**Antes**:
- Ancho: 2 pulgadas
- Alto máximo: 0.6 pulgadas
- **Problema**: Demasiado pequeño, poco visible

**Ahora**:
- Ancho: 3 pulgadas (aumento del 50%)
- Alto máximo: 0.9 pulgadas (aumento del 50%)
- **Resultado**: Logo institucional visible y profesional

```python
new_width = 3*inch  # Aumentado de 2 a 3 pulgadas
new_height = new_width * aspect
if new_height > 0.9*inch:  # Aumentado de 0.6 a 0.9
    new_height = 0.9*inch
    new_width = new_height / aspect
```

### 2. Márgenes Alternados (Mirror Margins)

**Concepto**: Para impresión a doble cara, los márgenes deben "alternarse" - el margen de encuadernación debe estar siempre del lado interior (donde se anilla/encuaderna).

**Implementación**:

#### Páginas Impares (1, 3, 5, 7...)
- **Margen izquierdo**: 5cm (encuadernación)
- **Margen derecho**: 2cm
- El margen ancho está a la izquierda

```python
frame_odd = Frame(
    50*mm,  # x1 - margen izquierdo ANCHO
    20*mm,  # y1
    A4[0] - 50*mm - 20*mm,  # width
    A4[1] - 30*mm - 20*mm,  # height
    id='odd'
)
```

#### Páginas Pares (2, 4, 6, 8...)
- **Margen izquierdo**: 2cm
- **Margen derecho**: 5cm (encuadernación)
- El margen ancho está a la derecha

```python
frame_even = Frame(
    20*mm,  # x1 - margen izquierdo NORMAL
    20*mm,  # y1
    A4[0] - 50*mm - 20*mm,  # width (mismo ancho de texto)
    A4[1] - 30*mm - 20*mm,  # height
    id='even'
)
```

### 3. BaseDocTemplate con PageTemplates

Se utiliza `BaseDocTemplate` en lugar de `SimpleDocTemplate` para permitir templates alternados:

```python
from reportlab.platypus.doctemplate import PageTemplate as PT, BaseDocTemplate

doc = BaseDocTemplate(
    buf,
    pagesize=A4,
    pageTemplates=[
        PT(id='odd', frames=[frame_odd]),
        PT(id='even', frames=[frame_even]),
    ]
)
```

## 📐 Especificaciones de Márgenes

### Vista en Impresión a Doble Cara

```
┌─────────────────────────────┐  ┌─────────────────────────────┐
│ Página 1 (impar)            │  │ Página 2 (par)              │
│                             │  │                             │
│ [5cm] Contenido     [2cm]   │  │ [2cm] Contenido      [5cm]  │
│   ↑                         │  │                          ↑   │
│ Encuadernación              │  │              Encuadernación  │
│                             │  │                             │
└─────────────────────────────┘  └─────────────────────────────┘
        ↓ Doblar aquí ↓
```

Cuando se dobla el documento para encuadernar:
- El margen de 5cm siempre queda del lado **interior** (encuadernación)
- El margen de 2cm siempre queda del lado **exterior** (borde libre)
- El texto mantiene el mismo ancho en todas las páginas

## 🎯 Beneficios

### 1. Impresión Profesional a Doble Cara
✅ Los márgenes se alternan correctamente
✅ El texto queda centrado visualmente cuando se abre el documento
✅ No hay pérdida de contenido en la encuadernación

### 2. Logo Más Visible
✅ 50% más grande que antes
✅ Mantiene proporciones correctas
✅ Más profesional e institucional

### 3. Optimización de Papel
✅ Permite impresión en ambas caras
✅ Reduce uso de papel a la mitad
✅ Más económico y ecológico

## 📊 Dimensiones Finales

### Logo
| Propiedad | Valor |
|-----------|-------|
| Ancho máximo | 3 pulgadas |
| Alto máximo | 0.9 pulgadas |
| Proporción | Automática |

### Márgenes - Páginas Impares
| Lado | Medida |
|------|--------|
| Izquierdo | 5cm |
| Derecho | 2cm |
| Superior | 3cm |
| Inferior | 2cm |

### Márgenes - Páginas Pares
| Lado | Medida |
|------|--------|
| Izquierdo | 2cm |
| Derecho | 5cm |
| Superior | 3cm |
| Inferior | 2cm |

### Ancho de Texto
- **Constante**: A4[0] - 50mm - 20mm ≈ 14cm
- **Igual en todas las páginas**

## 🔄 Alternancia de Páginas

El sistema automáticamente alterna entre templates:

1. **Página 1** → Template 'odd' (5cm izq, 2cm der)
2. **Página 2** → Template 'even' (2cm izq, 5cm der)
3. **Página 3** → Template 'odd' (5cm izq, 2cm der)
4. **Página 4** → Template 'even' (2cm izq, 5cm der)
5. Y así sucesivamente...

## 💡 Uso Recomendado

### Para Impresión
1. **Configurar impresora**: Impresión a doble cara (duplex)
2. **Orientación**: Voltear por el lado largo
3. **Encuadernación**: Por el lado izquierdo

### Para Visualización Digital
- El PDF se ve correctamente en pantalla
- Los márgenes alternados se aprecian al cambiar de página
- Simula correctamente cómo se verá impreso

## 🎉 Resultado

Los documentos ahora están optimizados para:
- ✅ **Impresión profesional a doble cara**
- ✅ **Logo institucional visible** (3" x 0.9")
- ✅ **Márgenes alternados automáticos**
- ✅ **Encuadernación sin pérdida de contenido**
- ✅ **Aspecto profesional tipo libro**

El sistema genera documentos listos para:
- Impresión en láser/inyección a doble cara
- Encuadernación con anillos, espiral o térmica
- Presentación judicial con formato profesional
- Archivo y conservación a largo plazo

**Estado**: ✅ OPTIMIZADO PARA IMPRESIÓN PROFESIONAL A DOBLE CARA
