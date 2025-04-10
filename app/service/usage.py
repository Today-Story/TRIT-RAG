from fastapi.responses import JSONResponse
from app.database.postgres import get_recommendations_by_user
from app.redis.usage import get_all_remaining_usage


def get_user_recommendation_history(user_id: int):
    try:
        history = get_recommendations_by_user(user_id)
        return JSONResponse(
            status_code=200,
            content={
                "code": "SUCCESS",
                "message": "Fetched recommendation history successfully.",
                "data": history
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "code": "ERROR",
                "message": f"Failed to fetch recommendation history: {str(e)}",
                "data": []
            }
        )


def get_user_remaining_usage(user_id: int):
    try:
        remaining = get_all_remaining_usage(user_id)
        return JSONResponse(
            status_code=200,
            content={
                "code": "SUCCESS",
                "message": "Remaining usage fetched successfully.",
                "data": {
                    "userId": user_id,
                    "remaining": remaining
                }
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "code": "ERROR",
                "message": f"Failed to fetch usage info: {str(e)}",
                "data": {}
            }
        )
