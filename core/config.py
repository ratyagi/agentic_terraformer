# Settings, constants
"""
core.config

Central configuration for Agentic Terraformer.
Sets up base paths, logging defaults, and simple global constants.
"""

import logging
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
MEMORY_DIR = BASE_DIR / "memory"
SESSIONS_DIR = MEMORY_DIR / "sessions"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for d in (DATA_DIR, MEMORY_DIR, SESSIONS_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Default config values
DEFAULT_REGION_ID = "coastal_city_01"

LOG_FILE = LOGS_DIR / "agent_events.log"
LOG_LEVEL = logging.INFO


def setup_logging() -> None:
    """Configure root logger for the application."""
    # Avoid duplicating handlers if called multiple times
    if logging.getLogger().handlers:
        return

    logging.basicConfig(
        filename=str(LOG_FILE),
        level=LOG_LEVEL,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logging.getLogger().addHandler(console_handler)
