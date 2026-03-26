FROM python:3.12-slim

WORKDIR /app

# Copia requirements primero → cachea pip install
COPY requirements.txt .

# Instala dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

EXPOSE 8080

# CMD corregido: formato shell para expansión de $PORT
CMD gunicorn --bind "0.0.0.0:$PORT" \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    main:app