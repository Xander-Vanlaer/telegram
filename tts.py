import io
from typing import Optional

from gtts import gTTS

from config import settings


def synthesize_speech(text: str, lang: Optional[str] = None) -> bytes:
    """Synthesize text to MP3 bytes using gTTS (no temp files)."""
    effective_lang = lang or settings.DEFAULT_LANG
    tts = gTTS(text=text, lang=effective_lang)
    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)
    return buffer.read()
