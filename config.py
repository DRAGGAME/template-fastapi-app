import os
from datetime import timedelta

from pydantic import SecretStr, Field
from pydantic_settings import SettingsConfigDict, BaseSettings


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="allow"
    )


class PostgresSettings(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="PG_")
    user: str
    password: SecretStr
    host: str
    port: int = 5432
    name: str
    database_schema: str = Field(default="public")


class RedisSettings(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str
    password: str
    port: int
    num_databases: int


class Config(BaseSettings):
    pg_settings: PostgresSettings = Field(default_factory=PostgresSettings)
    redis_settings: RedisSettings = Field(default_factory=RedisSettings)

    @classmethod
    def load(cls) -> "Config":
        return cls()