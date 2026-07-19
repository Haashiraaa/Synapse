# tests/conftest.py

import os
import pytest

from unittest.mock import patch, MagicMock

os.environ.setdefault(
    "TELEGRAM_TOKEN", "123456789:AAFakeTestTokenForUnitTests")
os.environ.setdefault("ALLOWED_CHAT_IDS", "-1001234567890,-1009876543210")
os.environ.setdefault("BOT_USERNAME", "SynapseTestBot")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-fake-key")
os.environ.setdefault(
    "DATABASE_URL", "postgresql://test:test@localhost:5432/synapse_test")
