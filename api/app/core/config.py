# File with environment variables and general configuration logic.
# Env variables are combined in nested groups like "Security", "Database" etc.
# Environment variables are case-insensitive
#
# Pydantic priority ordering:
#
# 1. (Most important, will overwrite everything) - environment variables
# 2. `.env` file in root folder of project
# 3. Default values
#
# See https://pydantic-docs.helpmanual.io/usage/settings/

from functools import lru_cache
from pathlib import Path
from typing import Literal, Union

from pydantic import AnyHttpUrl, BaseModel, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).parent.parent.parent.parent


class Security(BaseModel):
    jwt_issuer: str = "my-app"
    jwt_secret_key: SecretStr
    jwt_access_token_expire_secs: int = 24 * 3600  # 1d
    refresh_token_expire_secs: int = 28 * 24 * 3600  # 28d
    password_bcrypt_rounds: int = 12
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    backend_cors_origins: list[str] | list[AnyHttpUrl] = ["*"]
    root_username: str
    root_password: SecretStr


class MongoDB(BaseModel):
    host: str = "mongodb"
    port: int = 27017
    username: str
    password: SecretStr
    database: str = "app_db"
    auth_source: str = "admin"

    @computed_field
    def uri(self) -> str:
        """
        Constructs the MongoDB connection URI.
        Format: mongodb://username:password@host:port/database?authSource=admin
        """
        return (
            f"mongodb://{self.username}:"
            f"{self.password.get_secret_value()}@"
            f"{self.host}:{self.port}/"
            f"{self.database}?"
            f"authSource={self.auth_source}"
        )


class Riot(BaseModel):
    api_key: SecretStr
    rate_limiter_host: str
    rate_limiter_port: int

class Settings(BaseSettings):
    env: Literal["DEV", "PROD"] = "DEV"
    security: Security
    mongodb: MongoDB
    riot: Riot

    model_config = SettingsConfigDict(
        env_file=f"{PROJECT_DIR}/.env",
        case_sensitive=False,
        env_nested_delimiter="__",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()  # type: ignore
    
    if settings.env == "DEV":
        # Override MongoDB settings for development
        settings.mongodb.host = "localhost"
        settings.riot.rate_limiter_host = "localhost"

        # Add development CORS origins if not already present
        dev_origins = [
            "*",
        ]
        current_origins = [str(origin) for origin in settings.security.backend_cors_origins]
        for origin in dev_origins:
            if origin not in current_origins:
                settings.security.backend_cors_origins.append(origin)
        
        # Add development hosts if not already present
        dev_hosts = ["localhost", "127.0.0.1", "0.0.0.0"]
        for host in dev_hosts:
            if host not in settings.security.allowed_hosts:
                settings.security.allowed_hosts.append(host)

    return settings # type: ignore
