FROM node:20-alpine
WORKDIR /app

# Install curl for local health checks and debugging.
RUN apk add --no-cache curl

# Copy dependency manifests first to improve layer caching.
COPY package.json package-lock.json* ./

# Install from the lockfile for reproducible builds.
RUN npm ci

# Copy the rest of the application.
COPY . .

# Expose the Vite development port.
EXPOSE 5173

# Docker needs 0.0.0.0 inside the container, while compose binds the host port to localhost.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
