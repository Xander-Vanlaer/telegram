import os
import sqlite3
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class UserState:
    voice_enabled: bool = False
    last_location: Optional[str] = None


class StateStore:
    def __init__(self, db_path: Optional[str] = None):
        self._memory: Dict[int, UserState] = {}
        self._db_path = db_path
        if db_path:
            self._init_db(db_path)

    def _init_db(self, db_path: str) -> None:
        dir_name = os.path.dirname(db_path)
        os.makedirs(dir_name if dir_name else ".", exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_state (
                    user_id INTEGER PRIMARY KEY,
                    voice_enabled INTEGER NOT NULL DEFAULT 0,
                    last_location TEXT
                )
                """
            )
            conn.commit()

    def _load_from_db(self, user_id: int) -> Optional[UserState]:
        if not self._db_path:
            return None
        try:
            with sqlite3.connect(self._db_path) as conn:
                row = conn.execute(
                    "SELECT voice_enabled, last_location FROM user_state WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
            if row:
                return UserState(voice_enabled=bool(row[0]), last_location=row[1])
        except Exception:
            logger.exception("Failed to load state from DB for user %s", user_id)
        return None

    def _save_to_db(self, user_id: int, state: UserState) -> None:
        if not self._db_path:
            return
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO user_state (user_id, voice_enabled, last_location)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        voice_enabled = excluded.voice_enabled,
                        last_location = excluded.last_location
                    """,
                    (user_id, int(state.voice_enabled), state.last_location),
                )
                conn.commit()
        except Exception:
            logger.exception("Failed to save state to DB for user %s", user_id)

    def get(self, user_id: int) -> UserState:
        if user_id not in self._memory:
            loaded = self._load_from_db(user_id)
            self._memory[user_id] = loaded if loaded else UserState()
        return self._memory[user_id]

    def set(self, user_id: int, state: UserState) -> None:
        self._memory[user_id] = state
        self._save_to_db(user_id, state)
