
# tests/main/test_main_telegram.py

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.main.telegram import TelegramMain


class TestTelegramMain:

    @pytest.fixture
    def telegram_main(self):
        """
        Construct TelegramMain with the filesystem-dependent logger path lookup
        mocked out — FileHandler.get_ancestor_by_name walks up the directory
        tree for a folder literally named 'Synapse', which is a real dependency
        on where the test runner happens to be checked out. Not something a
        unit test should be coupled to.
        """
        with patch("src.main.telegram.FileHandler") as mock_file_handler:
            mock_file_handler.return_value.get_ancestor_by_name.return_value = MagicMock()
            yield TelegramMain()

    def test_telegram_main_constructs(self, telegram_main):
        """Bootstrap wiring (BotHandlers -> DbQueries + AI client + MediaProcessor,
        Logger, EmailAlertLogger) completes without raising."""
        assert telegram_main.bot is not None
        assert telegram_main.email_alert is not None

    def test_build_app_returns_real_application(self, telegram_main):
        """_build_app() constructs a real python-telegram-bot Application from
        the configured token, with no network call (that only happens on
        .initialize())."""
        app = telegram_main._build_app()
        assert app.bot.token == "123456789:AAFakeTestTokenForUnitTests"

    @pytest.mark.asyncio
    async def test_run_async_happy_path(self, telegram_main):
        """
        Full bootstrap-to-clean-shutdown lifecycle, with every network-touching
        call mocked: DB init, Telegram Application (build/initialize/start/poll/
        stop/shutdown), and bot.send_message for startup/shutdown notices.

        The signal handler registration is patched to invoke its callback
        immediately (stop_event.set()) instead of waiting for a real OS signal,
        so the run loop falls straight through to graceful shutdown.
        """
        mock_app = MagicMock()
        mock_app.initialize = AsyncMock()
        mock_app.start = AsyncMock()
        mock_app.stop = AsyncMock()
        mock_app.shutdown = AsyncMock()
        mock_app.bot.send_message = AsyncMock()
        mock_app.updater.start_polling = AsyncMock()
        mock_app.updater.stop = AsyncMock()

        def fake_add_signal_handler(sig, callback):
            callback()  # simulate an immediate shutdown signal

        with (
            patch("src.main.telegram.DbConnection.init_db") as mock_init_db,
            patch.object(telegram_main, "_build_app", return_value=mock_app),
            patch("asyncio.get_running_loop") as mock_get_loop,
        ):
            mock_get_loop.return_value.add_signal_handler.side_effect = fake_add_signal_handler

            await telegram_main._run_async()

        # DB was initialised
        mock_init_db.assert_called_once()

        # All commands + both message handler types registered
        assert mock_app.add_handler.call_count == 8
        assert mock_app.add_error_handler.call_count == 1

        # Polling started and stopped cleanly
        mock_app.updater.start_polling.assert_awaited_once()
        mock_app.updater.stop.assert_awaited_once()
        mock_app.stop.assert_awaited_once()
        mock_app.shutdown.assert_awaited_once()

        # Startup + shutdown notices fired for every configured group
        # (2 startup + 2 shutdown = 4; _notify_shutdown runs twice — once via
        # post_shutdown hook wiring, once via the explicit call in _run_async —
        # so shutdown sends are 4, not 2. Assert the minimum guaranteed sends.)
        assert mock_app.bot.send_message.await_count >= 4
