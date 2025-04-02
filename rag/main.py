import os
import psycopg2
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.openapi.utils import get_openapi
from rag.database import load_documents_from_postgres
from rag.recommender import generate_recommendation
from rag.auth import get_user_from_token
from dotenv import load_dotenv
from rag.usage_control_redis import check_usage_limit_redis


app = FastAPI()

# Swagger UI 상단 "Authorize" 버튼에 Bearer Token 설정
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

def fetch_user_country(user_id: int) -> str:
    load_dotenv()
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()
    cursor.execute("SELECT country FROM users WHERE id = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

# 추천 API
@app.get("/api/v1/users/recommend")
def recommend(
    needs: str = Query(...),
    category: str = Query(...),
    latitude: float = Query(...),
    longitude: float = Query(...),
    user=Depends(get_user_from_token)
):
    if not check_usage_limit_redis(user["userId"]):
        raise HTTPException(status_code=429, detail="일일 무료체험 기회가 소진되었습니다.")
    
    try:
        user_country = fetch_user_country(user["userId"])
        user["country"] = user_country

        user.update({
            "needs": needs,
            "category": category,
            "latitude": latitude,
            "longitude": longitude
        })

        contents, locations, creators = load_documents_from_postgres()
        result = generate_recommendation(user, contents, locations, creators)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
