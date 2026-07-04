
# src/storage/store.py

import re
import logging
from src.exceptions.errors import StorageError
from haashi_pkg.utility import Logger, FileHandler
from typing import Optional


class EnvStore:

    def __init__(
        self,
        logger: Optional[Logger] = None,
        handler: Optional[FileHandler] = None
    ) -> None:
        self.logger = logger or Logger(level=logging.INFO)
        self.handler = handler or FileHandler(logger=self.logger)
        self.project_root = self.handler.get_ancestor_by_name("Synapse")
        assert self.project_root is not None
        self.env_path = str(self.project_root / ".env")

    def _load_env(self) -> str:
        try:
            return self.handler.read_txt(self.env_path)
        except Exception as exc:
            raise StorageError("Failed to load .env!") from exc

    def _save_env(self, content: str) -> None:
        try:
            self.handler.save_txt(content, self.env_path)
        except Exception as exc:
            raise StorageError("Failed to save .env!") from exc

    def update_key(self, key: str, value: str) -> None:
        content = self._load_env()
        updated = re.sub(
            rf"^{key}=.*$",
            f"{key}={value}",
            content,
            flags=re.MULTILINE
        )
        self._save_env(updated)
