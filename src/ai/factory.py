

# src/ai/factory.py

from src.config.settings import Settings
from src.ai.base import BaseAIClient


def get_ai_client() -> BaseAIClient:
    provider = (Settings.AI_PROVIDER or "claude").lower()

    if provider not in ["claude", "openai"]:
        raise ValueError(f"Unknown AI provider: {provider}")

    if provider == "claude":
        from src.ai.claude.client import Claude
        return Claude()

    raise NotImplementedError("OpenAI is not yet implemented")
