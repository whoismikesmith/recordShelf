from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    """The source checkout containing this package, or the working directory otherwise.

    Lets `uv run recordshelf serve` find data/, config/, web/dist and .env no matter which
    directory it is started from.
    """
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / "src" / "recordshelf").is_dir():
            return parent
    return Path.cwd()


ROOT = _project_root()


class Settings(BaseSettings):
    """Process configuration. Read from environment and an optional .env file."""

    model_config = SettingsConfigDict(
        env_prefix="RECORDSHELF_",
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    discogs_username: str = Field(default="", validation_alias="DISCOGS_USERNAME")
    discogs_token: str = Field(default="", validation_alias="DISCOGS_TOKEN")
    data_dir: Path = ROOT / "data"
    layout_file: Path = ROOT / "config" / "shelf.yaml"
    web_dist: Path = ROOT / "web" / "dist"
    host: str = "0.0.0.0"
    port: int = 8000
    fps: int = 30
    user_agent: str = "recordShelf/2.0 (+https://github.com/whoismikesmith/recordShelf)"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "recordshelf.sqlite"
