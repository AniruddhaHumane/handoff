from pathlib import Path
from typing import Any


class RawAdapter:
    name = "raw"

    def __init__(self, root: Path) -> None:
        self.root = root

    def available(self) -> bool:
        return True

    def capture(self) -> dict[str, Any]:
        return {"adapter": self.name, "root": str(self.root)}
