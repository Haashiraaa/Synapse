

# src/db/connection.py

import psycopg2
from psycopg2.extras import RealDictCursor
from src.config.settings import Settings
from typing import Optional


class DbConnection:

    def __init__(self, settings: Optional[Settings] = None) -> None:

        self.settings = settings or Settings()
        self.db_url = self.settings.DATABASE_URL

    def get_conn(self) ->:
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
