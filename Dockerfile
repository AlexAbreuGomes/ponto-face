FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libgomp1 \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/

ENV DB_PATH=/data/ponto.db
ENV PHOTOS_DIR=/data/photos
ENV TEMPLATE_PATH=/data/template.npy
ENV INSIGHTFACE_HOME=/data/.insightface
ENV FACE_THRESHOLD=0.50

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
