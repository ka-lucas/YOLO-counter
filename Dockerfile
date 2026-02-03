FROM nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    libmariadb-dev-compat \
    libmariadb-dev \
    pkg-config \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libopus-dev \
    libvpx-dev \
    libsrtp2-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN curl -sS https://bootstrap.pypa.io/pip/3.8/get-pip.py | python3
RUN pip3 install --upgrade setuptools wheel

# Base dependencies
RUN pip3 install --no-cache-dir \
    numpy==1.24.3 \
    Cython

# WebRTC - INSTALAR av ANTES COM VERSÃO ESPECÍFICA
RUN pip3 install --no-cache-dir \
    av==10.0.0 \
    aiortc==1.9.0 \
    aiohttp==3.9.5

# OpenCV
RUN pip3 install --no-cache-dir opencv-python-headless==4.8.1.78

# Copiar requirements MODIFICADO (sem av e aiortc)
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Remover opencv-python se conflitar
RUN pip3 uninstall -y opencv-python opencv-contrib-python || true

# Verificar OpenCV
RUN echo "=== OpenCV instalado ===" && pip3 list | grep opencv
RUN python3 -c "import cv2; print('✓ OpenCV importado com sucesso')"

# Copiar código
COPY . .

# Static files
RUN mkdir -p /app/staticfiles
RUN python3 manage.py collectstatic --noinput --clear || true

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "300", "--preload"]