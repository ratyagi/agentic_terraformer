# Coordinates all agents
import logging
from typing import Any, Dict

from core.models import AgentMessage

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrator

    High-level controller that receives a START message from the UI or main
    program, kicks off the pipeline by sending a GOAL to PolicyAgent, and
    receives the final REPORT_READY from ReportAgent.

    This is also a good place to implement pause/resume and handle errors.
    """

    def handle_message(self, msg: AgentMessage, bus: "MessageBus") -> None:
        if msg.type == "START":
            self._handle_start(msg, bus)
        elif msg.type == "REPORT_READY":
            self._handle_report_ready(msg)
        else:
            logger.debug("Orchestrator ignoring message type %s", msg.type)

    def _handle_start(self, msg: AgentMessage, bus: "MessageBus") -> None:
        payload: Dict[str, Any] = msg.payload
        goal_text = payload["goal_text"]
        region_id = payload.get("region_id", "coastal_city_01")

        logger.info(
            "Orchestrator starting session %s for region %s",
            msg.session_id,
            region_id,
        )

        goal_msg = AgentMessage(
            sender="Orchestrator",
            receiver="PolicyAgent",
            type="GOAL",
            payload={"text": goal_text, "region_id": region_id},
            session_id=msg.session_id,
        )
        bus.send(goal_msg)

    def _handle_report_ready(self, msg: AgentMessage) -> None:
        report = msg.payload["report"]
        logger.info(
            "Orchestrator received final report for session %s: %s",
            msg.session_id,
            report.get("title", "Untitled"),
        )
        # In your UI, you might store this somewhere or push it to a client.
