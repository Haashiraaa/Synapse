

# src/db/queries.py

from src.db.connection import DbConnection
from typing import Dict, Any, Optional


class DbQueries:

    def get_or_create_conversation(self, chat_id: int) -> Dict[Any, Any]:
        with DbConnection.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM conversations WHERE chat_id = %s", (chat_id,)
                )
                row = cur.fetchone()
                if row:
                    return dict(row)

                cur.execute(
                    "INSERT INTO conversations (chat_id) VALUES (%s) RETURNING *",
                    (chat_id,),
                )
                conn.commit()
                return dict(cur.fetchone())

    def save_message(self, chat_id: int, role: str, content: str, user_name: Optional[str] = None):
        with DbConnection.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO messages (chat_id, role, content, user_name)
                       VALUES (%s, %s, %s, %s)""",
                    (chat_id, role, content, user_name),
                )
            conn.commit()

    def get_recent_messages(self, chat_id: int, limit: int = MESSAGE_WINDOW) -> list[dict]:
        """Returns messages oldest-first for the context window."""
        with DbConnection.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT role, content, user_name, created_at
                       FROM messages
                       WHERE chat_id = %s
                       ORDER BY created_at DESC
                       LIMIT %s""",
                    (chat_id, limit),
                )
                rows = cur.fetchall()
        return list(reversed(rows))  # flip to chronological

    def get_message_count(self, chat_id: int) -> int:
        with DbConnection.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) as cnt FROM messages WHERE chat_id = %s",
                    (chat_id,),
                )
                return cur.fetchone()["cnt"]

    def save_summary(self, chat_id: int, summary: str):
        with DbConnection.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE conversations
                       SET summary = %s, updated_at = NOW()
                       WHERE chat_id = %s""",
                    (summary, chat_id),
                )
            conn.commit()

    def prune_old_messages(self, chat_id: int, keep: int = MESSAGE_WINDOW):
        """Delete everything except the most recent `keep` messages."""
        with DbConnection.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """DELETE FROM messages
                       WHERE chat_id = %s
                         AND id NOT IN (
                             SELECT id FROM messages
                             WHERE chat_id = %s
                             ORDER BY created_at DESC
                             LIMIT %s
                         )""",
                    (chat_id, chat_id, keep),
                )
            conn.commit()
