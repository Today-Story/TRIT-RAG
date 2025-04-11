from fastapi import FastAPI, Query, Depends
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter

from app.core.auth import get_user_from_token
from app.service.user import handle_recommendation
from app.service.usage import (
    get_user_recommendation_history,
    get_user_remaining_usage
)
from app.monitoring.metrics import recommendation_failures_total

app = FastAPI()

# Prometheus exporter 등록
Instrumentator().instrument(app).expose(app)

# CORS 설정
origins = [
    "http://localhost:3000",
    "https://trit-dev.vercel.app",
    "https://trit-chi.vercel.app",
    "https://trit.app",
    "https://www.trit.app",
    "https://trit-test-only.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Swagger UI 상단 Authorize 버튼 활성화
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Trit Recommendation API",
        version="1.0.0",
        description="This is the API for personalized content/location recommendation",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 추천 요청 API
@app.get("/api/v1/users/recommend")
def recommend(
    needs: str = Query(...),
    category: str = Query(...),
    latitude: float = Query(...),
    longitude: float = Query(...),
    user=Depends(get_user_from_token)
):
    return handle_recommendation(user, needs, category, latitude, longitude)

# 추천 이력 조회 API
@app.get("/api/v1/users/recommend/history")
def get_recommendation_history(user=Depends(get_user_from_token)):
    return get_user_recommendation_history(user["userId"])

# 잔여 요청 횟수 조회 API
@app.get("/api/v1/users/usage")
def get_remaining_usage_all(user=Depends(get_user_from_token)):
    return get_user_remaining_usage(user["userId"])
