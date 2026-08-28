from pathlib import Path

from app.core.config import settings


class FileStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or settings.data_dir

    def path(self, *parts: str) -> Path:
        return self.base_dir.joinpath(*parts)

    def ensure_dir(self, *parts: str) -> Path:
        path = self.path(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path

