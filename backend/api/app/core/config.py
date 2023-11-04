import re
from pydantic import validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, Dict, List, Optional, Union
import os


env_file_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_file_path,
        env_file_encoding='utf-8',
        extra='ignore'
    )
    @validator('model_config', pre=True, check_fields=False)
    def validate_model_config(cls, v):
        if not isinstance(v, SettingsConfigDict):
            raise ValueError('model_config should be an instance of pydantic.BaseSettings')
        return v

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str
    @validator('PROJECT_NAME', pre=True)
    def validate_project_name(cls, v):
        if not v:
            raise ValueError('PROJECT_NAME is required')
        return v

    MONGODB_URI: str
    @validator('MONGODB_URI', pre=True)
    def validate_mongodb_uri(cls, v):
        if not re.match(r'^mongodb://[a-zA-Z0-9.-]+:[0-9]+/?$', v):
            raise ValueError('MONGODB_URI is not in the expected format')
        return v

    MONGODB_NAME: str
    @validator('MONGODB_NAME', pre=True)
    def validate_mongodb_name(cls, v):
        if not v:
            raise ValueError('MONGODB_NAME is required')
        return v

    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    RIOT_API_KEY: str
    @validator('RIOT_API_KEY', pre=True)
    def validate_riot_api_key(cls, v):
        if not re.match(r'^RGAPI-[a-zA-Z0-9-]+$', v):
            raise ValueError('RIOT_API_KEY is not in the expected format')
        return v

settings = Settings()
