# app/translate/router.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.service.translate_service import translate_text

router = APIRouter(prefix="/api/v1/translate", tags=["Translation"])

class TranslationRequest(BaseModel):
    text: str
    target_lang: str  # 예: "EN", "KO", "JA"

@router.post("")
async def translate(request: TranslationRequest):
    translated = await translate_text(request.text, request.target_lang)
    return {"translated": translated}

