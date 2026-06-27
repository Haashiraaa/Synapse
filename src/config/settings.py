

# src/config/settings.py

import os
from src.exceptions.errors import EnvVariableError
from dotenv import load_dotenv

load_dotenv()


class Settings:

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    BOT_USERNAME = os.getenv("BOT_USERNAME")  # e.g. @YourBotName
    MESSAGE_WINDOW = int(os.getenv("MESSAGE_WINDOW", 20)
                         )  # sliding window size

    # Email
    ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
    ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
    ALERT_EMAIL_PASSWORD = os.getenv("ALERT_EMAIL_PASSWORD")

    if not all([
        TELEGRAM_TOKEN,
        GROUP_CHAT_ID,
        ANTHROPIC_API_KEY,
        DATABASE_URL,
        BOT_USERNAME,

    ]):
        raise EnvVariableError(
            "Missing or invalid environment variables! Please check your .env file.")
