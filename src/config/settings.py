

# src/config/settings.py

import os
from src.exceptions.errors import EnvVariableError
from dotenv import load_dotenv

load_dotenv()


class Settings:

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    BOT_USERNAME = os.getenv("BOT_USERNAME")  # e.g. @YourBotName
    MESSAGE_WINDOW = int(os.getenv("MESSAGE_WINDOW", 20)
                         )  # sliding window size

    if not any([
        TELEGRAM_TOKEN,
        ANTHROPIC_API_KEY,
        DATABASE_URL,
        BOT_USERNAME,
    ]):
        raise EnvVariableError(
            "Missing or invalid environment variables! Please check your .env file.")
