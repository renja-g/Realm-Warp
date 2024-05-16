from functools import cached_property
from pathlib import Path
from typing import Literal, Union

from pydantic import AnyHttpUrl, MongoDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).parent.parent.parent.parent.parent


class Settings(BaseSettings):
    # CORE SETTINGS
    SECRET_KEY: str
    ENVIRONMENT: Literal['DEV', 'PYTEST', 'STG', 'PRD'] = 'DEV'
    SECURITY_BCRYPT_ROUNDS: int = 12
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 40320  # 28 days
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl | Literal['*']] = []
    ALLOWED_HOSTS: list[str] = ['localhost', '127.0.0.1']

    # PROJECT NAME, VERSION AND DESCRIPTION
    PROJECT_NAME: str = "Realm Warp"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Realm-Warp tracks summoner, match, and league data from Riot API, enhancing and storing it in MongoDB. It also offers an API for managing summoners and retrieving tracked summoner lists."

    # MONGODB
    DATABASE_HOSTNAME: str = 'localhost'
    MONGO_INITDB_ROOT_USERNAME: str
    MONGO_INITDB_ROOT_PASSWORD: str
    DATABASE_PORT: int = 27017
    DATABASE_DB: str = "watcher_db"

    # FIRST SUPERUSER
    SUPERUSER_USERNAME: str
    SUPERUSER_PASSWORD: str

    # PULSEFIRE SETTINGS
    RIOT_API_KEY: str
    RATELIMITER_HOST: str = 'localhost'
    RATELIMITER_PORT: int = 12227

    @computed_field
    @cached_property
    def DEFAULT_MONGODB_URI(self) -> str:
        return str(
            MongoDsn.build(
                scheme='mongodb',
                host=self.DATABASE_HOSTNAME,
                username=self.MONGO_INITDB_ROOT_USERNAME,
                password=self.MONGO_INITDB_ROOT_PASSWORD,
                port=self.DATABASE_PORT,
            )
        )

    model_config = SettingsConfigDict(env_file=f'{PROJECT_DIR}/.env', case_sensitive=True)


settings: Settings = Settings()  # type: ignore
