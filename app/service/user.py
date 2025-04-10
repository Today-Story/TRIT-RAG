from fastapi.responses import JSONResponse
from app.database.postgres import (
    load_documents_from_postgres,
    save_recommendation_to_db,
)
from app.redis.usage import (
    is_under_limit,
    increment_usage,
    get_remaining_usage,
)
from app.recommender.recommender import generate_recommendation
from prometheus_client import Counter
from app.database.postgres import fetch_user_country
from app.monitoring.metrics import recommendation_failures_total

def handle_recommendation(user: dict, needs: str, category: str, latitude: float, longitude: float):
    if not is_under_limit(user["userId"], needs):
        return JSONResponse(
            status_code=429,
            content={
                "code": "TOO_MANY_REQUESTS",
                "message": f"The daily free trial opportunity for {needs} has been used up.",
                "data": {
                    "userId": user["userId"],
                    "remaining": 0,
                    "message": {
                        "recommendation": {
                            "contentsId": None,
                            "creatorId": None,
                            "reason": f"The daily free trial opportunity for {needs} has been used up."
                        }
                    }
                }
            }
        )

    try:
        user_country = fetch_user_country(user["userId"])
        user.update({
            "country": user_country,
            "needs": needs,
            "category": category,
            "latitude": latitude,
            "longitude": longitude
        })

        contents, locations, creators = load_documents_from_postgres()
        result = generate_recommendation(user, contents, locations, creators)

        recommendation = result["message"]["recommendation"]
        success = (
            (needs == "contents" and recommendation["contentsId"] is not None) or
            (needs == "creator" and recommendation["creatorId"] is not None)
        )

        if success:
            increment_usage(user["userId"], needs)

            save_recommendation_to_db({
                "user_id": user["userId"],
                "needs": needs,
                "category": category,
                "contents_id": (
                    recommendation.get("contentsId", {}).get("contentsId")
                    if isinstance(recommendation.get("contentsId"), dict)
                    else recommendation.get("contentsId")
                ),
                "creator_id": (
                    recommendation.get("creatorId", {}).get("creatorId")
                    if isinstance(recommendation.get("creatorId"), dict)
                    else recommendation.get("creatorId")
                ),
                "reason": recommendation.get("reason")
            })
        else:
            recommendation_failures_total.inc()

        remaining_count = get_remaining_usage(user["userId"], needs)

        return JSONResponse(
            status_code=200,
            content={
                "code": "SUCCESS",
                "message": "Success!",
                "data": {
                    **result,
                    "remaining": {
                        needs: remaining_count
                    }
                }
            }
        )

    except Exception as e:
        recommendation_failures_total.inc()
        return JSONResponse(
            status_code=500,
            content={
                "code": "ERROR",
                "message": f"An error occurred while processing the recommendation.: {str(e)}",
                "data": {
                    "userId": user["userId"],
                    "remaining": get_remaining_usage(user["userId"], needs),
                    "message": {
                        "recommendation": {
                            "contentsId": None,
                            "creatorId": None,
                            "reason": f"Server error: {str(e)}"
                        }
                    }
                }
            }
        )
