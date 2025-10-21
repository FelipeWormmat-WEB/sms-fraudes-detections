FROM node:20-alpine
WORKDIR /app

# Instalar curl e outras dependências necessárias
RUN apk add --no-cache curl

# Copiar apenas manifestos de dependência primeiro para aproveitar o cache
COPY package.json package-lock.json* ./

# Instalar dependências
RUN npm install

# Copiar o restante do código
COPY . .

# Expor porta do Vite
EXPOSE 5173

# Rodar o Vite no modo dev escutando em 0.0.0.0 para aceitar conexões externas
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
