# src/config/settings.py

import os

from dotenv import load_dotenv

from src.exceptions.errors import EnvVariableError
from typing import Dict, Union

load_dotenv()


def _parse_chat_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError as exc:
            raise EnvVariableError(
                f"Invalid chat id '{part}' in ALLOWED_CHAT_IDS — "
                "must be a comma-separated list of integers."
            ) from exc
    return ids


class Settings:

    # Telegram
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    ALLOWED_CHAT_IDS: set[int] = _parse_chat_ids(os.getenv("ALLOWED_CHAT_IDS", ""))
    BOT_USERNAME = os.getenv("BOT_USERNAME")  # e.g. @YourBotName

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    AI_PROVIDER = os.getenv("AI_PROVIDER")

    DATABASE_URL = os.getenv("DATABASE_URL")
    MESSAGE_WINDOW = int(os.getenv("MESSAGE_WINDOW", 8))  # sliding window size

    # Email
    ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
    ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
    ALERT_EMAIL_PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD")

    _REQUIRED: Dict[str, Union[str, set[int], int, None]] = {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "ALLOWED_CHAT_IDS": ALLOWED_CHAT_IDS or None,
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
