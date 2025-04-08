FROM python:3.10-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 사전 설치: torch, transformers, numpy
RUN pip install --upgrade pip && \
    pip install --no-cache-dir torch>=2.1.0 transformers>=4.35.0 numpy<2

# 앱 복사
COPY . /app

# 나머지 라이브러리 설치
RUN pip install --no-cache-dir -r requirements.txt

# FastAPI 실행
CMD ["uvicorn", "rag.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
