# Stage 1: Builder
FROM python:3.11-slim AS builder

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependências Python no builder
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ----------------------
# Stage 2: Final image
# ----------------------
FROM python:3.11-slim

WORKDIR /app

# Copiar dependências do builder
COPY --from=builder /install /usr/local

# Dependência de runtime do scikit-learn (OpenMP)
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

# Copiar código
COPY . .

# Variáveis de ambiente padrão
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Criar usuário não-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

USER appuser

# Expor porta
EXPOSE 8000

# Comando default
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
