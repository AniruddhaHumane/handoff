from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AgentSnapshot:
    agent: str
    timestamp: str
    runtime: str = "unknown"
    summary: str = ""
    next_action: str = ""
    open_tasks: list[str] = field(default_factory=list)
    key_decisions: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    files_touched: list[str] = field(default_factory=list)
    files_read_first: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    confidence: str = "medium"
    uncertainties: list[str] = field(default_factory=list)
    provenance: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
    captured_summary: str = ""
    captured_open_tasks: list[str] = field(default_factory=list)
    captured_key_decisions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
