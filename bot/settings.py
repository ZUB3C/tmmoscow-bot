from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

from bot.utils import PathControl


class Settings(BaseSettings):
    bot_token: SecretStr
    drop_pending_updates: bool
    admin_chat_id: list[int]

    postgres_host: str
    postgres_db: str
    postgres_password: SecretStr
    postgres_port: int
    postgres_user: str
    postgres_data: str

    model_config = SettingsConfigDict(env_file=PathControl.get(".env"), env_file_encoding="utf-8")

    def build_dsn(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )
