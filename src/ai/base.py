# src/ai/base.py

from abc import ABC, abstractmethod
from typing import Any


class BaseAIClient(ABC):
    """
    Abstract interface for AI provider clients.
    Any provider (Claude, OpenAI, etc.) must implement these methods.
    """

    def __init__(self) -> None:
        self._MODEL: str = self.get_model("sonnet")

    @abstractmethod
    def get_reply(
        self, chat_id: int, media: list[dict[Any, Any]] | None = None, caption: str = ""
    ) -> str:
        """
        Build context from DB and return the AI's reply to the latest message.
        Accepts chat_id so the provider can fetch conversation history itself.
        """
        ...

    @abstractmethod
    def summarise(self, chat_id: int) -> str:
        """
        Summarise the current conversation window for the given chat.
        Returns the summary text — caller is responsible for saving it.
        """
        ...

    def get_model(self, model: str) -> str:

        claude_model_map = {"sonnet": "claude-sonnet-4-6", "haiku": "claude-haiku-4-5"}
        return claude_model_map.get(model.lower(), "claude-sonnet-4-6")
