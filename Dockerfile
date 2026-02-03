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

# Install packages with NumPy < 2.0 to avoid compatibility issues
RUN pip install --no-cache-dir \
    "numpy<2.0" \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    python-multipart==0.0.9 \
    opencv-python-headless==4.9.0.80 \
    Pillow==10.2.0 \
    onnxruntime==1.16.3 \
    insightface==0.7.3 \
    firebase-admin==6.4.0 \
    cryptography==42.0.2 \
    python-dotenv==1.0.0

COPY main.py .

EXPOSE 8000

# 🔥 عدّلي هذا السطر فقط:
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
