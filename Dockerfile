FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (200MB instead of 2.5GB)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Then install everything else
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY frontend/ frontend/

RUN mkdir -p uploads chroma_data

EXPOSE 8001

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8001"]