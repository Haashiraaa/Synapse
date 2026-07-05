

# src/main.py

import sys
import logging
import signal
import asyncio
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

    async def _notify_startup(self, app: Application[Any, Any, Any, Any, Any, Any]) -> None:
        await app.bot.send_message(
            chat_id=Settings.ALLOWED_CHAT_ID,
            text="Synapse is back online and ready to go."
        )

    async def _notify_shutdown(self, app: Application[Any, Any, Any, Any, Any, Any]) -> None:
        await app.bot.send_message(
            chat_id=Settings.ALLOWED_CHAT_ID,
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

    async def _run_async(self) -> None:

        DbConnection.init_db(self.logger)
        app = self._build_app()

        app.add_handler(CommandHandler("start", self.bot.cmd_start))
        app.add_handler(CommandHandler("summary", self.bot.cmd_summary))
        app.add_handler(CommandHandler("clear", self.bot.cmd_clear))
        app.add_handler(CommandHandler("model", self.bot.cmd_model))
        app.add_handler(CommandHandler(
            "switchmodel", self.bot.cmd_switch_model))
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, self.bot.handle_message))
        app.add_handler(MessageHandler(
            filters.PHOTO | filters.Document.ALL, self.bot.handle_media))

        app.add_error_handler(self._error_handler)
        app.post_shutdown = self._notify_shutdown

        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)

        await app.initialize()
        await app.start()

        assert app.updater is not None
        await app.updater.start_polling()

        try:
            self.email_alert.alert_bot_started()
        except (EmailAuthError, EmailDeliveryError) as exc:
            self.logger.error(
                f"Failed to send start alert: {exc}", exception=exc, save_to_json=True)

        try:
            await self._notify_startup(app)
        except Exception as exc:
            self.logger.error(
                f"Failed to send startup notification: {exc}", exception=exc, save_to_json=True)

        self.logger.info("Bot is running...")
        await stop_event.wait()

        self.logger.info("Shutdown signal received. Stopping gracefully...")
        await app.updater.stop()
        await app.stop()
        await self._notify_shutdown(app)   # bot connection still alive here
        await app.shutdown()
        self.logger.info("Shutdown complete.")

    def run(self) -> None:
        try:
            asyncio.run(self._run_async())
        except KeyboardInterrupt:
            self.logger.info("Force-interrupted.")
            sys.exit(0)


def main() -> None:
    Main().run()
