

# src/config/settings.py

import os
from src.exceptions.errors import EnvVariableError
from dotenv import load_dotenv

load_dotenv()


class Settings:

    # Telegram
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", 0))
    BOT_USERNAME = os.getenv("BOT_USERNAME")  # e.g. @YourBotName

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    AI_PROVIDER = os.getenv("AI_PROVIDER")

    DATABASE_URL = os.getenv("DATABASE_URL")
    MESSAGE_WINDOW = int(os.getenv("MESSAGE_WINDOW", 8)
                         )  # sliding window size

    # Email
    ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
    ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
    ALERT_EMAIL_PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD")

    _REQUIRED = {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "ALLOWED_CHAT_ID": ALLOWED_CHAT_ID,
        "BOT_USERNAME": BOT_USERNAME,
        "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
        "DATABASE_URL": DATABASE_URL,
    }

    _missing = [name for name, value in _REQUIRED.items() if not value]
    if _missing:
        raise EnvVariableError(
            "Missing required environment variables: "
            + ", ".join(_missing)
            + ". Copy .env.example to .env and fill these in."
        )
