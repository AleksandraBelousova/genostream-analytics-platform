import os
from contextlib import contextmanager
from typing import Generator
from clickhouse_driver import Client
from pydantic_settings import BaseSettings

class ClickHouseSettings(BaseSettings):
    host: str
    db: str
    user: str
    password: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
settings = ClickHouseSettings()
@contextmanager
def get_db_session() -> Generator[Client, None, None]:
    client = None
    try:
        client = Client.from_url(
            f'clickhouse://{settings.user}:{settings.password}@{settings.host}/{settings.db}'
        )
        yield client
    except Exception as e:
        print(f"FATAL: Database connection failed. Error: {e}")
        raise