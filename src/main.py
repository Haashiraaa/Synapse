

# src/main.py

import sys
import logging
from haashi_pkg.utility import Logger
from src.db.connection import DbConnection
from src.telegram.handlers import BotHandlers
from src.config.settings import Settings
from src.exceptions.errors import EmailAuthError, EmailDeliveryError
from src.loggers.email_logger import EmailAlertLogger
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
        self.email_alert = EmailAlertLogger(self.logger)

    def _build_app(self) -> Application[Any, Any, Any, Any, Any, Any]:
        return ApplicationBuilder().token(cast(str, Settings.TELEGRAM_TOKEN)).build()

    async def _notify_shutdown(self, app: Application[Any, Any, Any, Any, Any, Any]) -> None:
        await app.bot.send_message(
            chat_id=Settings.GROUP_CHAT_ID,
            text="🔧 Bot is going down for maintenance. We'll be back shortly!"
        )
        try:
            self.email_alert.alert_bot_stopped(
                reason="Process was interrupted by user!")
        except (EmailAuthError, EmailDeliveryError) as exc:
            self.logger.error(
                f"Failed to send shutdown alert: {exc}", exception=exc, save_to_json=True)

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.logger.error(
            f"Exception: {context.error}", exception=context.error, save_to_json=True)

        try:
            self.email_alert.alert_error(cast(str, context.error))
        except (EmailAuthError, EmailDeliveryError) as exc:
            self.logger.error(
                f"Failed to send error alert: {exc}", exception=exc, save_to_json=True)
            pass

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
            self.email_alert.alert_bot_started()
            app.run_polling()

        except (EmailAuthError, EmailDeliveryError) as exc:
            self.logger.error(
                f"Failed to send start alert: {exc}", exception=exc, save_to_json=True)
            pass

        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            sys.exit(0)
