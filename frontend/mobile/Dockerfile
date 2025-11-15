FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --ignore-scripts --no-fund --no-audit
COPY . .
CMD ["npm", "run", "dev"]
