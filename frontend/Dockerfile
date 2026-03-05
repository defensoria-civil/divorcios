# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Instalar dependencias
COPY package*.json ./
RUN npm install

# Copiar código y build
COPY . .
RUN npm run build

# Production stage
FROM nginx:stable-alpine

# Copiar archivos del build al directorio de nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copiar configuración de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
