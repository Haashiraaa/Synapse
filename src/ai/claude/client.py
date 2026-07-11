# src/ai/claude/client.py

from typing import Any, cast

from anthropic import Anthropic
from anthropic.types import MessageParam, TextBlock

from src.ai.base import BaseAIClient
from src.ai.prompt import SYSTEM_PROMPT
from src.config.settings import Settings
from src.db.queries import DbQueries


class Claude(BaseAIClient):
    """
    Claude (Anthropic) implementation of BaseAIClient.
    Owns all Claude-specific API logic: context assembly, reply generation,
    and conversation summarisation.
    """

    def __init__(self) -> None:

        super().__init__()
        self._client = Anthropic(api_key=Settings.ANTHROPIC_API_KEY)
        self._db = DbQueries()

        self._SUMMARY_MAX_TOKENS = 1536
        self._REPLY_MAX_TOKENS = 4096
        self._SUMMARY_SOFT_CAP_WORDS = 900
        self._SUMMARY_MODEL = self.get_model("haiku")

    # ── public interface (implements BaseAIClient) ────────────────────────────

    def get_reply(
        self, chat_id: int, media: list[dict[Any, Any]] | None = None, caption: str = ""
    ) -> str:
        """
        Assemble the message context for chat_id and return Claude's reply.
        Raises anthropic.APIError on failure — let the caller handle it.
        """
        messages = self._build_messages(chat_id)

        if media and messages:
            last = messages[-1]
            text_part = caption or (
                last["content"] if isinstance(last["content"], str) else "")
            last["content"] = cast(
                Any, [{"type": "text", "text": text_part}] + media)

        response = self._client.messages.create(
            model=self._MODEL,
            max_tokens=self._REPLY_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages,
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
            f"{m['user_name'] or m['role']}: {m['content']}" for m in recent)
        prev_summary = convo.get("summary", "")

        if len(prev_summary.split()) > self._SUMMARY_SOFT_CAP_WORDS:
            prompt = (
                f"Current running summary (has grown too long):\n{prev_summary}\n\n"
                f"New messages to fold in:\n{history_text}\n\n"
                "This summary has grown too large and needs compacting. Rewrite it "
                "tighter: drop anything resolved, outdated, or no longer relevant — "
                "closed questions, decisions already acted on, dated logistics that "
                "have passed. Keep durable facts, standing decisions, unresolved open "
                "questions, and anything someone would need to know to avoid repeating "
                f"themselves. Fold in the new messages too. Target roughly "
                f"{self._SUMMARY_SOFT_CAP_WORDS // 2} words. Dense bullet points, "
                "grouped by topic, attributed by name where relevant."
                "When referencing code, describe the change or decision rather than pasting the "
                "snippet verbatim — e.g. 'fixed the race condition in the pruning logic by "
                "decoupling keep from the trigger threshold' rather than reproducing the diff."
            )
        else:
            prompt = (
                f"Previous summary (running memory of the conversation):\n"
                f"{prev_summary or '(none yet — this is the first summary)'}\n\n"
                f"New messages to fold in:\n{history_text}\n\n"
                "Update the summary above to incorporate the new messages. This is a "
                "persistent memory, not a fresh recap: preserve every fact, decision, "
                "commitment, and open question from the previous summary UNLESS the new "
                "messages explicitly resolve, contradict, or supersede it. Do not "
                "re-compress or drop old information just to save space — only trim "
                "something if it's genuinely resolved or no longer relevant. Use dense "
                "topic-grouped bullet points rather than prose, and attribute anything "
                "person-specific. There is no fixed word limit — let it grow if the "
                "conversation genuinely has more going on."
                "When referencing code, describe the change or decision rather than pasting the "
                "snippet verbatim — e.g. 'fixed the race condition in the pruning logic by "
                "decoupling keep from the trigger threshold' rather than reproducing the diff."
            )

        response = self._client.messages.create(
            model=self._SUMMARY_MODEL,
            max_tokens=self._SUMMARY_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        return self._extract_text(response.content)

    # ── private helpers ───────────────────────────────────────────────────────

    def _extract_text(self, content: list[Any]) -> str:
        """Narrow the response content union to the first TextBlock's text."""
        for block in content:
            if isinstance(block, TextBlock):
                return block.text
        raise ValueError("No TextBlock found in response content")

    def _build_messages(self, chat_id: int) -> list[MessageParam]:
        """
        Assemble the messages list for the Claude API call.
        Injects an existing summary as the first exchange if one exists,
        then appends the recent sliding window in chronological order.
        """
        convo = self._db.get_or_create_conversation(chat_id)
        recent = self._db.get_recent_messages(chat_id)

        messages: list[MessageParam] = []

        summary = convo.get("summary", "").strip()
        if summary:
            messages.append(
                {
                    "role": "user",
                    "content": f"[Conversation summary so far]\n{summary}",
                }
            )
            messages.append(
                {
                    "role": "assistant",
                    "content": "Got it, I have context from the earlier conversation.",
                }
            )

        for m in recent:
            if m["role"] == "user":
                prefix = f"{m['user_name']}: " if m["user_name"] else ""
                messages.append(
                    {"role": "user", "content": prefix + m["content"]})
            else:
                messages.append({"role": "assistant", "content": m["content"]})

        return messages
