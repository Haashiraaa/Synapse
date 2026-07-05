# src/loggers/base.py

from abc import ABC, abstractmethod


class BaseAlertLogger(ABC):

    @abstractmethod
    def send(self, subject: str, body: str) -> None:
        """Send an alert. Raise on failure."""
        ...

    def alert_error(self, error: str) -> None:
        self.send(subject="✖️ Synapse — Error", body=f"An error occurred:\n\n{error}")

    def alert_bot_started(self) -> None:
        self.send(subject="🤖 Synapse — Bot Started", body="Synapse is now live.")

    def alert_bot_stopped(self, reason: str = "Unknown") -> None:
        self.send(
            subject="🛑 Synapse — Bot Stopped",
            body=f"Synapse has stopped running.\n\nReason: {reason}",
        )
