FROM python:3.10-bullseye

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .

RUN pip install --no-cache-dir fastapi==0.109.0 && \
    pip install --no-cache-dir uvicorn[standard]==0.27.0 && \
    pip install --no-cache-dir python-multipart==0.0.9 && \
    pip install --no-cache-dir numpy==1.24.3 && \
    pip install --no-cache-dir opencv-python-headless==4.9.0.80 && \
    pip install --no-cache-dir Pillow==10.2.0 && \
    pip install --no-cache-dir onnxruntime==1.16.3 && \
    pip install --no-cache-dir insightface==0.7.3 && \
    pip install --no-cache-dir firebase-admin==6.4.0 && \
    pip install --no-cache-dir cryptography==42.0.2 && \
    pip install --no-cache-dir python-dotenv==1.0.0

COPY main.py .

EXPOSE 8000

CMD sh -c "python main.py"
