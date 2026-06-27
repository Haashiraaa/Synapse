

# src/ai/factory.py

from src.config.settings import Settings
from src.ai.base import BaseAIClient
from typing import Optional


def get_ai_client() -> Optional[BaseAIClient]:
    provider = (Settings.AI_PROVIDER or "claude").lower()

    if provider not in ["claude", "openai"]:
        raise ValueError(f"Unknown AI provider: {provider}")

    if provider == "claude":
        from src.ai.claude.client import Claude
        return Claude()
    elif provider == "openai":
        # from src.ai.openai.client import OpenAI
        # return OpenAI()
        pass
