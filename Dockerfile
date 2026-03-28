FROM python:3.11-slim

# ==============================
# VARIABLES DE ENTORNO
# ==============================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ==============================
# DIRECTORIO DE TRABAJO
# ==============================
WORKDIR /app

# ==============================
# DEPENDENCIAS DEL SISTEMA
# ==============================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ==============================
# DEPENDENCIAS PYTHON
# ==============================
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ==============================
# COPIAR PROYECTO
# ==============================
COPY . .

# ==============================
# PUERTO
# ==============================
EXPOSE 8000

# ==============================
# COMANDO DE ARRANQUE
# ==============================
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]