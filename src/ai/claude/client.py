

# src/ai/client.py

# src/ai/claude/client.py

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlock
from src.ai.base import BaseAIClient
from src.ai.prompt import SYSTEM_PROMPT
from src.config.settings import Settings
from src.db.queries import DbQueries
from typing import List, Any


class Claude(BaseAIClient):
    """
    Claude (Anthropic) implementation of BaseAIClient.
    Owns all Claude-specific API logic: context assembly, reply generation,
    and conversation summarisation.
    """

    _MODEL = "claude-sonnet-4-6"
    _SUMMARY_MAX_TOKENS = 500
    _REPLY_MAX_TOKENS = 1000

    def __init__(self) -> None:
        self._client = Anthropic(api_key=Settings.ANTHROPIC_API_KEY)
        self._db = DbQueries()

    # ── public interface (implements BaseAIClient) ────────────────────────────

    def get_reply(self, chat_id: int) -> str:
        """
        Assemble the message context for chat_id and return Claude's reply.
        Raises anthropic.APIError on failure — let the caller handle it.
        """
        messages = self._build_messages(chat_id)

        response = self._client.messages.create(
            model=self._MODEL,
            max_tokens=self._REPLY_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages
        )

        return self._extract_text(response.content)

    def summarise(self, chat_id: int) -> str:
        """
        Summarise the current message window for chat_id.
        Returns the summary text — does NOT save or prune; caller owns that.
        """
        convo = self._db.get_or_create_conversation(chat_id)
        recent = self._db.get_recent_messages(
            chat_id, limit=Settings.MESSAGE_WINDOW)

        if not recent:
            return ""

        history_text = "\n".join(
            f"{m['user_name'] or m['role']}: {m['content']}" for m in recent
        )
        prev_summary = convo.get("summary", "")

        prompt = (
            f"Previous summary:\n{prev_summary}\n\n"
            f"New messages:\n{history_text}\n\n"
            "Write a concise summary (max 300 words) of the entire conversation so far, "
            "capturing key decisions, code snippets discussed, open questions, and who said what."
        )

        response = self._client.messages.create(
            model=self._MODEL,
            max_tokens=self._SUMMARY_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        return self._extract_text(response.content)

    # ── private helpers ───────────────────────────────────────────────────────

    def _extract_text(self, content: List[Any]) -> str:
        """Narrow the response content union to the first TextBlock's text."""
        for block in content:
            if isinstance(block, TextBlock):
                return block.text
        raise ValueError("No TextBlock found in response content")

    def _build_messages(self, chat_id: int) -> List[MessageParam]:
        """
        Assemble the messages list for the Claude API call.
        Injects an existing summary as the first exchange if one exists,
        then appends the recent sliding window in chronological order.
        """
        convo = self._db.get_or_create_conversation(chat_id)
        recent = self._db.get_recent_messages(chat_id)

        messages: List[MessageParam] = []

        summary = convo.get("summary", "").strip()
        if summary:
            messages.append({
                "role": "user",
                "content": f"[Conversation summary so far]\n{summary}",
            })
            messages.append({
                "role": "assistant",
                "content": "Got it, I have context from the earlier conversation.",
            })

        for m in recent:
            if m["role"] == "user":
                prefix = f"{m['user_name']}: " if m["user_name"] else ""
                messages.append(
                    {"role": "user", "content": prefix + m["content"]})
            else:
                messages.append({"role": "assistant", "content": m["content"]})

        return messages
