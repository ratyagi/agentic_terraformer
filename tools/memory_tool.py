# Long-term memory access & context compaction
"""
tools.memory_tool

Simple "long-term memory" utilities for Agentic Terraformer.

Stores compact summaries of runs and provides basic retrieval and
context compaction.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from core.config import MEMORY_DIR

logger = logging.getLogger(__name__)

LONG_TERM_FILE = MEMORY_DIR / "long_term.json"


def _load_long_term() -> Dict[str, Any]:
    if not LONG_TERM_FILE.exists():
        return {"sessions": []}

    with LONG_TERM_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "sessions" not in data or not isinstance(data["sessions"], list):
        data["sessions"] = []
    return data


def _save_long_term(data: Dict[str, Any]) -> None:
    LONG_TERM_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LONG_TERM_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.debug("Saved long-term memory to %s", LONG_TERM_FILE)


def append_session_summary(
    session_id: str,
    region_id: str,
    co2_reduction_percent: float,
    total_cost_usd: float,
    score: float,
) -> None:
    """
    Append a compact summary for a completed session.
    """
    data = _load_long_term()
    summary = {
        "session_id": session_id,
        "region_id": region_id,
        "co2_reduction_percent": co2_reduction_percent,
        "total_cost_usd": total_cost_usd,
        "score": score,
    }
    data["sessions"].append(summary)
    _save_long_term(data)
    logger.info(
        "Appended long-term memory summary for session %s (region=%s)",
        session_id,
        region_id,
    )


def get_recent_summaries(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Return most recent `limit` session summaries.
    """
    data = _load_long_term()
    sessions = data.get("sessions", [])
    return sessions[-limit:]


def summarize_patterns() -> Dict[str, Any]:
    """
    Produce a very simple "context compaction" summary: averages and best values.
    """
    data = _load_long_term()
    sessions = data.get("sessions", [])
    if not sessions:
        return {
            "num_sessions": 0,
            "avg_co2_reduction_percent": 0.0,
            "avg_total_cost_usd": 0.0,
            "best_score": None,
        }

    n = len(sessions)
    total_red = sum(s["co2_reduction_percent"] for s in sessions)
    total_cost = sum(s["total_cost_usd"] for s in sessions)
    best_score = max(s["score"] for s in sessions)

    summary = {
        "num_sessions": n,
        "avg_co2_reduction_percent": total_red / n,
        "avg_total_cost_usd": total_cost / n,
        "best_score": best_score,
    }

    logger.debug("Computed long-term summary: %s", summary)
    return summary
