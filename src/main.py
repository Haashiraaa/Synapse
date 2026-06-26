

# src/main.py

import sys
import logging
from haashi_pkg.utility import Logger
from src.db.connection import DbConnection
from src.telegram.handlers import BotHandlers
from src.config.settings import Settings
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
from typing import Any, cast


class Main:

    def __init__(self) -> None:
        self.bot = BotHandlers()
        self.logger = Logger(level=logging.INFO)

    def _build_app(self) -> Application[Any, Any, Any, Any, Any, Any]:
        return ApplicationBuilder().token(cast(str, Settings.TELEGRAM_TOKEN)).build()

    async def _notify_shutdown(self, app: Application[Any, Any, Any, Any, Any, Any]) -> None:
        await app.bot.send_message(
            chat_id=Settings.GROUP_CHAT_ID,
            text="🔧 Bot is going down for maintenance. We'll be back shortly!"
        )

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.logger.error(f"Exception: {context.error}")
        self.logger.error(exception=context.error, save_to_json=True)
        if isinstance(update, Update) and update.message:
            await update.message.reply_text("⚠️ Something went wrong. Try again.")

    def run(self) -> None:

        DbConnection.init_db(self.logger)
        app = self._build_app()

        app.add_handler(CommandHandler("start", self.bot.cmd_start))
        app.add_handler(CommandHandler("summary", self.bot.cmd_summary))
        app.add_handler(CommandHandler("clear", self.bot.cmd_clear))
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.bot.handle_message))

        app.add_error_handler(self._error_handler)
        app.post_shutdown = self._notify_shutdown

        try:
            self.logger.info("Bot is running...")
            app.run_polling()
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            sys.exit(0)
