FROM node:20-alpine

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar archivos de configuración
COPY tailwind.config.js postcss.config.js vite.config.js ./

# Copiar código fuente
COPY index.html ./
COPY src ./src

# Exponer puerto
EXPOSE 3000

# Comando para desarrollo
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
