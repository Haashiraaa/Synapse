
# src/loggers/base.py

from abc import ABC, abstractmethod


class BaseAlertLogger(ABC):

    @abstractmethod
    def send(self, subject: str, body: str) -> None:
        """Send an alert. Raise on failure."""
        ...
