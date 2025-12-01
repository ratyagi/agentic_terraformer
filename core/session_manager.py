# Session + state management
"""
core.session_manager

Session creation, saving, loading, and status updates.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from uuid import uuid4
from datetime import datetime

from core.config import SESSIONS_DIR, DEFAULT_REGION_ID
from core.models import SessionState

logger = logging.getLogger(__name__)


def _session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def start_session(goal_text: str, region_id: Optional[str] = None) -> SessionState:
    """
    Create a new session, save it to disk, and return its state.
    """
    if region_id is None:
        region_id = DEFAULT_REGION_ID

    session_id = str(uuid4())
    now = datetime.utcnow().isoformat() + "Z"

    state = SessionState(
        session_id=session_id,
        goal_text=goal_text,
        region_id=region_id,
        status="created",
        created_at=now,
        updated_at=now,
        metadata={},
    )

    save_session(state)
    logger.info("Created new session %s for region %s", session_id, region_id)
    return state


def load_session(session_id: str) -> Optional[SessionState]:
    """
    Load session state from disk. Returns None if not found.
    """
    path = _session_path(session_id)
    if not path.exists():
        logger.warning("Session file not found for %s", session_id)
        return None

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    state = SessionState.from_dict(data)
    logger.info("Loaded session %s (status=%s)", session_id, state.status)
    return state


def save_session(state: SessionState) -> None:
    """
    Save session state to disk as JSON.
    """
    path = _session_path(state.session_id)
    state.updated_at = datetime.utcnow().isoformat() + "Z"

    with path.open("w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2)

    logger.debug("Saved session %s (status=%s)", state.session_id, state.status)


def update_session_status(session_id: str, status: str) -> Optional[SessionState]:
    """
    Convenience helper to update only the status field.
    """
    state = load_session(session_id)
    if state is None:
        return None

    state.status = status
    save_session(state)
    logger.info("Updated session %s status -> %s", session_id, status)
    return state
