# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 복사
COPY . /app

# 환경변수용 dotenv
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# FastAPI 실행
CMD ["uvicorn", "rag.main:app", "--host", "0.0.0.0", "--port", "8000"]
