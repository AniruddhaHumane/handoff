from pathlib import Path
from typing import Any, Protocol


class Adapter(Protocol):
    name: str

    def available(self) -> bool: ...

    def capture(self) -> dict[str, Any]: ...


def read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""
