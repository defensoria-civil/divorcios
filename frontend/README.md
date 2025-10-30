# Dashboard Frontend - Defensoría Civil

Dashboard web profesional para operadores de la Defensoría Civil de San Rafael, Mendoza.

## 🚀 Quick Start

```bash
# 1. Instalar dependencias
npm install

# 2. Iniciar servidor de desarrollo
npm run dev

# 3. Abrir en el navegador
# http://localhost:5173
```

## 🏗️ Stack Tecnológico

- **React 18** con TypeScript
- **Vite** - Build tool
- **TailwindCSS** - Estilos
- **React Router v6** - Navegación
- **TanStack Query** - Gestión de estado servidor
- **Zustand** - Gestión de estado cliente
- **React Hook Form** + **Zod** - Formularios
- **Lucide React** - Iconos

## 📁 Estructura del Proyecto

```
src/
├── app/                    # Configuración de la aplicación
│   ├── App.tsx
│   ├── router.tsx
│   └── providers.tsx
│
├── features/               # Módulos por funcionalidad
│   ├── auth/              # Autenticación
│   ├── cases/             # Gestión de casos
│   ├── metrics/           # Dashboard y métricas
│   └── users/             # Gestión de usuarios
│
├── shared/                # Componentes y utilidades compartidas
│   ├── components/
│   │   ├── ui/           # Componentes UI reutilizables
│   │   └── Layout/       # Layouts
│   ├── hooks/            # Hooks personalizados
│   └── utils/            # Utilidades
│
├── lib/                   # Librerías y configuración
└── styles/               # Estilos globales
```

## 🔑 Credenciales de Prueba

Por ahora el backend no tiene autenticación completa. Para desarrollo:

- Email: `operador@test.com`
- Password: `password123`

## 🎨 Características

### ✅ Implementadas (Fase 1)
- ✅ Sistema de autenticación con JWT
- ✅ Roles y permisos (Operador, Supervisor, Admin)
- ✅ Dark mode
- ✅ Layout responsive con sidebar
- ✅ Dashboard básico con métricas
- ✅ Rutas protegidas por autenticación

### 🚧 En Desarrollo (Fase 2-3)
- Gestión completa de casos
- Vista de conversaciones
- Intervención manual
- Métricas avanzadas con gráficos
- Exportación CSV
- Monitoreo en tiempo real

## 🛠️ Scripts Disponibles

```bash
# Desarrollo
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview

# Linting
npm run lint
```

## 🌓 Dark Mode

El dark mode está implementado y se persiste en localStorage. Toggle en el header.

## 🔒 Sistema de Permisos

El sistema implementa 3 roles con permisos granulares:

- **Operador**: Ver casos propios, editar, exportar
- **Supervisor**: Ver todos los casos, asignar, métricas globales
- **Admin**: Control total del sistema

## 📝 Variables de Entorno

Ver `.env.example` para la configuración requerida:

```env
VITE_API_URL=http://localhost:8000
```

## 🐛 Troubleshooting

### Error: Cannot find module '@/*'
Asegúrate de que `tsconfig.json` tenga configurado el path alias correctamente.

### API no responde
Verifica que el backend esté corriendo en `http://localhost:8000`

## 📚 Próximos Pasos

1. Instalar dependencias: `npm install`
2. Iniciar dev server: `npm run dev`
3. Conectar con el backend
4. Continuar con Fase 2: Gestión de Casos

---

**Desarrollado para la Defensoría Civil de San Rafael, Mendoza, Argentina**
