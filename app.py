import io
import logging
from typing import Optional

import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ai_client import chat_completion
from config import settings
from state import StateStore, UserState
from tts import synthesize_speech
from weather import (
    extract_location_and_days,
    fetch_current_weather,
    fetch_forecast,
    is_weather_query,
    summarize_current_weather,
    summarize_tomorrow_forecast,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
store = StateStore(db_path=settings.SQLITE_DB_PATH if settings.SQLITE_DB_PATH else None)

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"


# ---------------------------------------------------------------------------
# Telegram helpers
# ---------------------------------------------------------------------------

def send_message(chat_id: int, text: str) -> None:
    url = f"{TELEGRAM_API_BASE}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception:
        logger.exception("Failed to send message to chat %s", chat_id)


def send_voice(chat_id: int, voice_bytes: bytes, caption: Optional[str] = None) -> None:
    url = f"{TELEGRAM_API_BASE}/sendVoice"
    files = {"voice": ("voice.mp3", io.BytesIO(voice_bytes), "audio/mpeg")}
    data = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption
    try:
        resp = requests.post(url, data=data, files=files, timeout=30)
        resp.raise_for_status()
    except Exception:
        logger.exception("Failed to send voice to chat %s", chat_id)


def reply(chat_id: int, user_id: int, text: str) -> None:
    """Send text or voice depending on user preference."""
    state = store.get(user_id)
    if state.voice_enabled:
        try:
            voice_bytes = synthesize_speech(text)
            send_voice(chat_id, voice_bytes, caption=text[:1024])
            return
        except Exception:
            logger.exception("TTS failed for user %s; falling back to text", user_id)
    send_message(chat_id, text)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return JSONResponse(content={"status": "ok"})


@app.post(settings.WEBHOOK_PATH)
async def receive_webhook(request: Request):
    try:
        update = await request.json()
    except Exception:
        logger.exception("Failed to parse webhook body")
        return JSONResponse(content={"status": "ok"})

    logger.info("Received update: %s", update)

    message = update.get("message")
    if not message:
        return JSONResponse(content={"status": "ok"})

    chat_id: int = message.get("chat", {}).get("id")
    user_id: int = message.get("from", {}).get("id", chat_id)
    text: str = (message.get("text") or "").strip()

    if not text or not chat_id:
        return JSONResponse(content={"status": "ok"})

    normalized = text.lower()

    # --- voice toggle commands ---
    if normalized in ("voice on", "/voice_on"):
        state = store.get(user_id)
        state.voice_enabled = True
        store.set(user_id, state)
        reply(chat_id, user_id, "Voice mode enabled. I will now respond with voice messages.")
        return JSONResponse(content={"status": "ok"})

    if normalized in ("voice off", "/voice_off"):
        state = store.get(user_id)
        state.voice_enabled = False
        store.set(user_id, state)
        send_message(chat_id, "Voice mode disabled. I will now respond with text messages.")
        return JSONResponse(content={"status": "ok"})

    # --- weather queries ---
    if is_weather_query(text):
        try:
            location, days = extract_location_and_days(text)
            if not location:
                state = store.get(user_id)
                location = state.last_location
            if not location:
                send_message(chat_id, "Please include a city name in your weather request, e.g. 'weather Brussels'.")
                return JSONResponse(content={"status": "ok"})

            state = store.get(user_id)
            state.last_location = location
            store.set(user_id, state)

            if days <= 0:
                data = fetch_current_weather(location)
                response_text = summarize_current_weather(data)
            else:
                data = fetch_forecast(location)
                response_text = summarize_tomorrow_forecast(data)

            reply(chat_id, user_id, response_text)
        except requests.HTTPError as exc:
            logger.exception("OpenWeather error for user %s", user_id)
            send_message(chat_id, f"Sorry, I couldn't fetch the weather data. ({exc.response.status_code})")
        except Exception:
            logger.exception("Unexpected weather error for user %s", user_id)
            send_message(chat_id, "Sorry, something went wrong while fetching the weather.")
        return JSONResponse(content={"status": "ok"})

    # --- general AI queries ---
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Keep your answers concise and friendly. "
                    "Respond in plain text without markdown formatting."
                ),
            },
            {"role": "user", "content": text},
        ]
        response_text = chat_completion(messages)
        reply(chat_id, user_id, response_text)
    except requests.HTTPError as exc:
        logger.exception("OpenAI error for user %s", user_id)
        send_message(chat_id, f"Sorry, I couldn't get a response from the AI. ({exc.response.status_code})")
    except Exception:
        logger.exception("Unexpected AI error for user %s", user_id)
        send_message(chat_id, "Sorry, something went wrong while processing your request.")

    return JSONResponse(content={"status": "ok"})
