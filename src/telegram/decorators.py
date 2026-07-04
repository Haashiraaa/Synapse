
# src/telegram/decorators.py


from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from src.config.settings import Settings
from collections.abc import Callable, Coroutine
from typing import Any

Handler = Callable[
    [Any, Update, ContextTypes.DEFAULT_TYPE],
    Coroutine[Any, Any, None]
]


def restricted(func: Handler) -> Handler:
    @wraps(func)
    async def wrapper(
        self: Any,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:

        chat_id = update.effective_chat.id if update.effective_chat else None

        if chat_id != int(Settings.ALLOWED_CHAT_ID):
            return

        await func(self, update, context)

    return wrapper
