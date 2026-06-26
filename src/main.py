

# src/main.py

import logging
from haashi_pkg.utility import Logger
from src.telegram.handlers import BotHandlers
from src.config.settings import Settings
from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters
from typing import Any, cast


class Main:

    def __init__(self) -> None:
        self.bot = BotHandlers()
        self.logger = Logger(level=logging.INFO)

    def _build_app(self) -> Application[Any, Any, Any, Any, Any, Any]:
        return ApplicationBuilder().token(cast(str, Settings.TELEGRAM_TOKEN)).build()

    def run(self) -> None:

        app = self._build_app()

        app.add_handler(CommandHandler("start", self.bot.cmd_start))
        app.add_handler(CommandHandler("summary", self.bot.cmd_summary))
        app.add_handler(CommandHandler("clear", self.bot.cmd_clear))
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.bot.handle_message))

        self.logger.info("Bot is running...")
        app.run_polling()
