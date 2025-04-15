from app.translate.deepl_service import translate_text

def translate_text_sync(text: str, target_lang: str = "KO") -> str:
    import asyncio
    return asyncio.run(translate_text(text, target_lang))
