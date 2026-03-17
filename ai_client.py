import logging
from typing import List, Dict

import requests

from config import settings

logger = logging.getLogger(__name__)


def chat_completion(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
