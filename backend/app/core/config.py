from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="QUANT_")

    app_name: str = "CapitalA"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    project_root: Path = Path(__file__).resolve().parents[3]
    data_dir: Path = project_root / "data"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
