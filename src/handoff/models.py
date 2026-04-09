from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Manifest:
    schema_version: str = "1"
    active_adapter: str = "raw"
    created_at: str = ""
    updated_at: str = ""
    last_checkpoint_at: str | None = None
    last_resume_at: str | None = None
    integrity: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SessionState:
    goal: str = ""
    status: str = "idle"
    next_action: str = ""
    active_mode: str | None = None
    timestamp: str = ""
    last_checkpoint_at: str | None = None
    last_adapter_used: str = "raw"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
