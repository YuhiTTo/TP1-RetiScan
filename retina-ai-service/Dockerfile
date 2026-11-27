FROM python:3.11-slim

# Configuración de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Directorio principal del proyecto
WORKDIR /opt/retiscan

# Dependencias del sistema para TensorFlow y OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias del servicio IA
COPY retina-ai-service/requirements.txt /tmp/requirements.txt

# Instalar dependencias
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && python -m pip install --no-cache-dir "tensorflow[and-cuda]==2.21.0"

# Copiar código, modelos y calibradores permitidos
COPY . /opt/retiscan/

# Configurar Python
ENV PYTHONPATH=/opt/retiscan/retina-ai-service

# Directorio del servicio IA
WORKDIR /opt/retiscan/retina-ai-service

# Puerto del servicio
EXPOSE 8001

# Configurar bibliotecas NVIDIA y arrancar FastAPI
CMD ["bash", "-lc", "SITE_PACKAGES=\"$(python -c 'import site; print(site.getsitepackages()[0])')\"; NVIDIA_LIB_PATHS=\"$(find \"$SITE_PACKAGES/nvidia\" -mindepth 2 -maxdepth 2 -type d -name lib -printf '%p:' 2>/dev/null | sed 's/:$//')\"; if [ -d /usr/lib/wsl/lib ]; then NVIDIA_LIB_PATHS=\"/usr/lib/wsl/lib:${NVIDIA_LIB_PATHS}\"; fi; export LD_LIBRARY_PATH=\"${NVIDIA_LIB_PATHS}:${LD_LIBRARY_PATH:-}\"; exec uvicorn app.main:app --host 0.0.0.0 --port 8001"]