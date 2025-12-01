# Message schemas, dataclasses
# This is the A2A simple protocol
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class AgentMessage:
    sender: str
    receiver: str
    type: str          # e.g. "GOAL", "DATA_REQUEST", "SCENARIO_PROPOSAL"
    payload: Dict[str, Any]
    session_id: str
