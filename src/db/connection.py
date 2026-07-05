# src/db/connection.py

import psycopg2
from haashi_pkg.utility import Logger
from psycopg2.extras import RealDictCursor

from src.config.settings import Settings


class DbConnection:

    @classmethod
    def get_conn(cls) -> psycopg2.extensions.connection:
        return psycopg2.connect(Settings.DATABASE_URL, cursor_factory=RealDictCursor)

    @classmethod
    def test_conn(cls, logger: Logger) -> None:
        with cls.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                logger.info(f"Connection successful: {result}")

    @classmethod
    def init_db(cls, logger: Logger) -> None:
        with cls.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT UNIQUE NOT NULL,
                        summary TEXT DEFAULT '',
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );

                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        chat_id BIGINT NOT NULL,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                        content TEXT NOT NULL,
                        user_name TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );

                    CREATE INDEX IF NOT EXISTS idx_messages_chat_id
                        ON messages (chat_id, created_at DESC);
                """)
            conn.commit()
        logger.info("DB initialised")
