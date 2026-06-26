
# src/ai/base.py

from abc import ABC, abstractmethod


class BaseAIClient(ABC):

    """
    Abstract interface for AI provider clients.
    Any provider (Claude, OpenAI, etc.) must implement these methods.
    """

    @abstractmethod
    def get_reply(self, chat_id: int) -> str:
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
