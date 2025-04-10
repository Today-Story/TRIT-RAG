#!/bin/bash

# FastAPI 로컬 개발 서버 실행 (app.main:app)
# PYTHONPATH를 루트로 설정해 모듈 인식 오류 해결

echo "🚀 Starting FastAPI with PYTHONPATH=."
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
