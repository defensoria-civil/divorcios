# 🚀 Guía Rápida: Componentes Magic UI

## 📖 Uso Básico

### 1. NumberTicker - Números Animados

```tsx
import NumberTicker from '@/shared/components/magicui/NumberTicker';

// Básico
<NumberTicker value={42} />

// Con estilos personalizados
<NumberTicker 
  value={1234} 
  className="text-4xl font-bold text-blue-600"
/>

// Con decimales
<NumberTicker 
  value={99.99} 
  decimalPlaces={2}
/>

// Con delay
<NumberTicker 
  value={500} 
  delay={0.5} // segundos
/>

// De arriba hacia abajo
<NumberTicker 
  value={100} 
  direction="down"
/>
```

**Casos de uso:**
- Métricas en dashboards
- Contadores de usuarios
- Estadísticas en tiempo real
- Precios dinámicos

---

### 2. ShimmerButton - Botones Premium

```tsx
import ShimmerButton from '@/shared/components/magicui/ShimmerButton';

// Básico (fondo negro por defecto)
<ShimmerButton onClick={handleClick}>
  Click Me
</ShimmerButton>

// Gradiente azul (recomendado)
<ShimmerButton 
  onClick={handleDownload}
  background="linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)"
  shimmerColor="#60a5fa"
>
  Descargar
</ShimmerButton>

// Gradiente verde
<ShimmerButton 
  background="linear-gradient(135deg, #10b981 0%, #059669 100%)"
  shimmerColor="#34d399"
>
  Confirmar
</ShimmerButton>

// Gradiente rojo (destructivo)
<ShimmerButton 
  background="linear-gradient(135deg, #ef4444 0%, #dc2626 100%)"
  shimmerColor="#f87171"
>
  Eliminar
</ShimmerButton>

// Con tamaños personalizados
<ShimmerButton 
  className="h-12 px-8 text-lg"
  shimmerDuration="2s"
>
  Large Button
</ShimmerButton>
```

**Casos de uso:**
- Botones de CTA (Call to Action)
- Acciones importantes
- Descargas de documentos
- Formularios de conversión

---

### 3. BlurFade - Transiciones Suaves

```tsx
import BlurFade from '@/shared/components/magicui/BlurFade';

// Básico
<BlurFade>
  <div>Contenido que aparece suavemente</div>
</BlurFade>

// Con delay
<BlurFade delay={0.2}>
  <Card>Aparece después de 0.2s</Card>
</BlurFade>

// Múltiples elementos con stagger
{items.map((item, index) => (
  <BlurFade key={item.id} delay={index * 0.1}>
    <Card>{item.content}</Card>
  </BlurFade>
))}

// Animación al scroll (inView)
<BlurFade inView delay={0.1}>
  <div>Aparece cuando scrolleas hasta aquí</div>
</BlurFade>

// Personalizado
<BlurFade 
  delay={0.3}
  duration={0.6}
  yOffset={12}
  blur="8px"
>
  <div>Animación más pronunciada</div>
</BlurFade>
```

**Casos de uso:**
- Cards en dashboards
- Listas de elementos
- Secciones de página
- Modales y diálogos
- Elementos al scroll

---

## 🎨 Combinaciones Recomendadas

### Dashboard Card con Métrica
```tsx
<BlurFade delay={0.1}>
  <Card className="p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-600">Total Usuarios</p>
        <NumberTicker 
          value={totalUsers} 
          className="text-3xl font-bold"
        />
      </div>
      <div className="p-3 bg-blue-100 rounded-lg">
        <Users className="w-6 h-6 text-blue-600" />
      </div>
    </div>
  </Card>
</BlurFade>
```

### Botón de Acción Principal
```tsx
<ShimmerButton 
  onClick={handleSubmit}
  background="linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)"
  shimmerColor="#60a5fa"
  className="w-full h-12"
>
  <Check className="w-5 h-5 mr-2" />
  Confirmar y Continuar
</ShimmerButton>
```

### Lista Animada
```tsx
<div className="space-y-4">
  {cases.map((case_, index) => (
    <BlurFade key={case_.id} delay={0.05 + index * 0.05} inView>
      <Card className="p-4 hover:shadow-lg transition-shadow">
        <h3>{case_.title}</h3>
        <p>{case_.description}</p>
      </Card>
    </BlurFade>
  ))}
</div>
```

---

## ⚙️ Configuraciones Avanzadas

### NumberTicker con Formato Personalizado
```tsx
// Moneda
<NumberTicker 
  value={1234.56} 
  decimalPlaces={2}
  className="text-2xl font-bold text-green-600"
/>
// Muestra: 1.234,56

// Porcentaje
<div className="flex items-center">
  <NumberTicker value={87} />
  <span className="ml-1">%</span>
</div>
```

### ShimmerButton Estados
```tsx
// Disabled
<ShimmerButton disabled>
  No disponible
</ShimmerButton>

// Loading con spinner
<ShimmerButton disabled>
  <div className="animate-spin mr-2">⏳</div>
  Procesando...
</ShimmerButton>
```

### BlurFade Condicional
```tsx
{isLoading ? (
  <Spinner />
) : (
  <BlurFade>
    <Content />
  </BlurFade>
)}
```

---

## 🎯 Mejores Prácticas

### 1. Delays Escalonados
```tsx
// ✅ CORRECTO: Delays progresivos
<BlurFade delay={0.1}><Card1 /></BlurFade>
<BlurFade delay={0.2}><Card2 /></BlurFade>
<BlurFade delay={0.3}><Card3 /></BlurFade>

// ❌ INCORRECTO: Todos al mismo tiempo
<BlurFade><Card1 /></BlurFade>
<BlurFade><Card2 /></BlurFade>
<BlurFade><Card3 /></BlurFade>
```

### 2. Usar inView para Listas Largas
```tsx
// ✅ CORRECTO: Solo anima cuando es visible
{items.map((item, i) => (
  <BlurFade key={item.id} delay={i * 0.05} inView>
    <Item data={item} />
  </BlurFade>
))}

// ❌ INCORRECTO: Anima todo de inmediato
{items.map((item, i) => (
  <BlurFade key={item.id} delay={i * 0.05}>
    <Item data={item} />
  </BlurFade>
))}
```

### 3. ShimmerButton Solo en CTAs
```tsx
// ✅ CORRECTO: Acción principal
<ShimmerButton onClick={handleSubmit}>
  Enviar Formulario
</ShimmerButton>

// ❌ INCORRECTO: Acción secundaria
<ShimmerButton onClick={handleCancel}>
  Cancelar
</ShimmerButton>
```

---

## 🚫 Errores Comunes

### Error 1: Demasiadas Animaciones
```tsx
// ❌ MAL: Sobrecarga visual
<BlurFade>
  <ShimmerButton>
    <NumberTicker value={count} />
  </ShimmerButton>
</BlurFade>

// ✅ BIEN: Animación única y clara
<BlurFade delay={0.1}>
  <Button>
    {count}
  </Button>
</BlurFade>
```

### Error 2: Delays Muy Largos
```tsx
// ❌ MAL: Usuario espera demasiado
<BlurFade delay={2.0}>
  <ImportantContent />
</BlurFade>

// ✅ BIEN: Aparece rápidamente
<BlurFade delay={0.2}>
  <ImportantContent />
</BlurFade>
```

### Error 3: No Usar Key en Listas
```tsx
// ❌ MAL: Problemas de rendering
{items.map((item, i) => (
  <BlurFade delay={i * 0.1}>
    <Card />
  </BlurFade>
))}

// ✅ BIEN: Key único
{items.map((item, i) => (
  <BlurFade key={item.id} delay={i * 0.1}>
    <Card />
  </BlurFade>
))}
```

---

## 🎨 Paleta de Gradientes Recomendados

```tsx
// Azul (Primary)
background="linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)"
shimmerColor="#60a5fa"

// Verde (Success)
background="linear-gradient(135deg, #10b981 0%, #059669 100%)"
shimmerColor="#34d399"

// Morado (Premium)
background="linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)"
shimmerColor="#a78bfa"

// Naranja (Warning)
background="linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"
shimmerColor="#fbbf24"

// Rojo (Danger)
background="linear-gradient(135deg, #ef4444 0%, #dc2626 100%)"
shimmerColor="#f87171"

// Gris (Neutral)
background="linear-gradient(135deg, #6b7280 0%, #4b5563 100%)"
shimmerColor="#9ca3af"
```

---

## 📱 Responsive Considerations

```tsx
// NumberTicker responsive
<NumberTicker 
  value={count}
  className="text-2xl md:text-3xl lg:text-4xl font-bold"
/>

// ShimmerButton responsive
<ShimmerButton className="w-full md:w-auto px-4 md:px-8">
  Acción
</ShimmerButton>

// BlurFade delays responsive
const isMobile = window.innerWidth < 768;
<BlurFade delay={isMobile ? 0 : 0.2}>
  <Content />
</BlurFade>
```

---

## 🔧 Troubleshooting

### Problema: Animaciones no se ven
**Solución:** Verifica que Framer Motion esté instalado
```bash
npm install framer-motion
```

### Problema: ShimmerButton no tiene efecto
**Solución:** Verifica que las animaciones CSS estén en globals.css

### Problema: BlurFade no anima en scroll
**Solución:** Añade la prop `inView`
```tsx
<BlurFade inView>...</BlurFade>
```

### Problema: Performance lenta
**Solución:** Limita animaciones simultáneas
```tsx
// Limita a 10 items con animación
{items.slice(0, 10).map((item, i) => (
  <BlurFade key={item.id} delay={i * 0.05}>
    <Item />
  </BlurFade>
))}
```

---

## 📚 Recursos Adicionales

- **Documentación Completa:** Ver `ANALISIS_MAGIC_UI.md`
- **Implementación Fase 1:** Ver `IMPLEMENTACION_MAGIC_UI_FASE1.md`
- **Ejemplos en Vivo:** Dashboard.tsx, CaseDetail.tsx, CasesList.tsx

---

**Última actualización:** 06/11/2025
