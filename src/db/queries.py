

# src/db/queries.py

from src.db.connection import DbConnection
from src.config.settings import Settings
from typing import Dict, Any, Optional, List, Union
from psycopg2.extras import RealDictRow


class DbQueries:

    def get_or_create_conversation(self, chat_id: int) -> Union[Dict[Any, Any], RealDictRow]:
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
                row = cur.fetchone()
                return dict(row) if row else {}

    def save_message(self, chat_id: int, role: str, content: str, user_name: Optional[str] = None):
        with DbConnection.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO messages (chat_id, role, content, user_name)
                       VALUES (%s, %s, %s, %s)""",
                    (chat_id, role, content, user_name),
                )
            conn.commit()

    def get_recent_messages(self, chat_id: int, limit: int = Settings.MESSAGE_WINDOW) -> List[Dict[Any, Any]]:
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
        # flip to chronological
        return list(reversed([dict(row) for row in rows])) if rows else []

    def get_message_count(self, chat_id: int) -> int:
        with DbConnection.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) as cnt FROM messages WHERE chat_id = %s",
                    (chat_id,),
                )
                row = cur.fetchone()
                return int(row["cnt"]) if row else 0  # type: ignore

    def save_summary(self, chat_id: int, summary: str) -> None:
        with DbConnection.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE conversations
                       SET summary = %s, updated_at = NOW()
                       WHERE chat_id = %s""",
                    (summary, chat_id),
                )
            conn.commit()

    def prune_old_messages(self, chat_id: int, keep: int = Settings.MESSAGE_WINDOW) -> None:
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

    def clear_history(self, chat_id: int) -> None:
        with DbConnection.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM messages WHERE chat_id = %s", (chat_id,)
                )
            conn.commit()
