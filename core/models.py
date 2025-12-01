# Message schemas, dataclasses
# This is the A2A simple protocol
"""
core.models

Shared data models for messages and session state.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class AgentMessage:
    """
    AgentMessage

    Generic agent-to-agent message used as the A2A protocol.
    """
    sender: str
    receiver: str
    type: str
    payload: Dict[str, Any]
    session_id: str
    timestamp: Optional[str] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            # ISO timestamp
            self.timestamp = datetime.utcnow().isoformat() + "Z"


@dataclass
class SessionState:
    """
    SessionState

    Tracks the high-level state of a session, for pause/resume and inspection.
    """
    session_id: str
    goal_text: str
    region_id: str
    status: str = "created"   # e.g. created, running, completed, error
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self) -> None:
        now = datetime.utcnow().isoformat() + "Z"
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        return cls(**data)
