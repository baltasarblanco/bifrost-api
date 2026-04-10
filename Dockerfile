# Etapa 1: Constructor (Build)
FROM python:3.12-slim as builder

WORKDIR /app

# Instalamos dependencias del sistema necesarias para psycopg2 y compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Etapa 2: Ejecución (Runtime)
FROM python:3.12-slim

WORKDIR /app

# Solo instalamos la librería de PostgreSQL necesaria para correr
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*

# Copiamos las librerías instaladas de la etapa anterior
COPY --from=builder /install /usr/local

# Copiamos el código de la app
COPY . .

# Exponemos el puerto que usará AWS App Runner o EC2
EXPOSE 8000

# Comando para arrancar (usamos 0.0.0.0 para que sea accesible desde afuera)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]