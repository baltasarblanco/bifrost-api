# 1. Usar una imagen oficial de Python ligera como base
FROM python:3.12-slim

# 2. Definir el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar el inventario de dependencias
COPY requirements.txt .

# 4. Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto de tu código fuente al contenedor
COPY . .

# 6. Exponer el puerto por donde habla FastAPI
EXPOSE 8000

# 7. El comando de encendido
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
