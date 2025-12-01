# Save/load reports, scenarios, logs
"""
tools.storage_tool

Utilities for saving and loading reports and other persistent artifacts.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from core.config import MEMORY_DIR, SESSIONS_DIR

logger = logging.getLogger(__name__)

REPORTS_DIR = MEMORY_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _report_path(session_id: str) -> Path:
    return REPORTS_DIR / f"{session_id}_report.json"


def save_report(session_id: str, report: Dict[str, Any]) -> None:
    """
    Save a report dict as JSON for a given session.
    """
    path = _report_path(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Saved report for session %s to %s", session_id, path)


def load_report(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a report dict for a given session. Returns None if not found.
    """
    path = _report_path(session_id)
    if not path.exists():
        logger.warning("Report not found for session %s", session_id)
        return None

    with path.open("r", encoding="utf-8") as f:
        report = json.load(f)

    logger.info("Loaded report for session %s from %s", session_id, path)
    return report
