FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# PyTorch só de CPU, para a imagem ficar menor
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[web]"

# Baixa os pesos oficiais na construção da imagem
RUN python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"

EXPOSE 8000
CMD ["yolo-counter", "serve", "--host", "0.0.0.0", "--port", "8000"]
