import jwt
from fastapi import Header, HTTPException
from typing import Annotated
from app.core.config import settings

ALGORITHM = "HS256"
SECRET_KEY = settings.JWT_SECRET

def get_user_from_token(
    authorization: Annotated[str, Header(..., include_in_schema=False)]
):
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token format")

        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        return {
            "userId": payload.get("userIdentity"),
            "name": payload.get("userId"),
            "age": None,
            "gender": None,
            "country": None
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
