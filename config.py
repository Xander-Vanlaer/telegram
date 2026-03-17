from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = ""
    OPENAI_API_KEY: str = ""
    OPENWEATHER_API_KEY: str = ""
    WEBHOOK_BASE_URL: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook/telegram"
    SQLITE_DB_PATH: str = "data/state.db"
    DEFAULT_LANG: str = "en"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
