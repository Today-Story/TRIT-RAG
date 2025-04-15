import httpx
from app.core.config import settings

DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

async def translate_text(text: str, target_lang: str = "KO") -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            DEEPL_API_URL,
            data={
                "auth_key": settings.DEEPL_API_KEY,
                "text": text,
                "target_lang": target_lang
            }
        )
        result = response.json()
        return result["translations"][0]["text"]
