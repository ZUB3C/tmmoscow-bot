from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from bot.utils import PathControl


class Settings(BaseSettings):
    bot_token: SecretStr
    drop_pending_updates: bool
    admin_chat_id: list[int]

    sqlite_db_file: Path

    model_config = SettingsConfigDict(env_file=PathControl.get(".env"), env_file_encoding="utf-8")

    def build_sqlite_url(self) -> str:
        return f"sqlite+aiosqlite:///{PathControl.get(self.sqlite_db_file)}"
