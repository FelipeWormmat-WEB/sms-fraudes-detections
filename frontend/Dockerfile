# Frontend (Vite + React) Dev Server
FROM node:20-alpine

WORKDIR /app

# Copiar apenas manifestos de dependência primeiro para aproveitar o cache
COPY package.json package-lock.json* ./

# Instalar dependências
# Usamos npm install ao invés de npm ci para funcionar mesmo sem lockfile
RUN npm install

# Copiar o restante do código
COPY . .

# Expor porta do Vite
EXPOSE 5173

# Rodar o Vite no modo dev escutando em 0.0.0.0 para aceitar conexões externas
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
