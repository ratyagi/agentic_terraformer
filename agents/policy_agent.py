# Interprets goals & policies (LLM)
# Goal: Turn a human query into a structured sustainability objective.
import logging
from typing import Any, Dict

from core.models import AgentMessage

logger = logging.getLogger(__name__)


class PolicyAgent:
    """
    PolicyAgent

    Takes a high-level natural language sustainability goal and produces
    a structured policy/goal specification for downstream agents.

    In a real system, this would use an LLM. Here we implement a simple
    rule-based parser that you can later replace with an LLM call.
    """

    def __init__(self, default_region_id: str = "coastal_city_01"):
        self.default_region_id = default_region_id

    def handle_message(self, msg: AgentMessage, bus: "MessageBus") -> None:
        if msg.type != "GOAL":
            logger.debug("PolicyAgent ignoring message type %s", msg.type)
            return

        goal_text = msg.payload.get("text", "")
        region_id = msg.payload.get("region_id", self.default_region_id)

        logger.info("PolicyAgent received GOAL for region %s: %s", region_id, goal_text)

        policy = self._generate_policy(goal_text, region_id)

        out_msg = AgentMessage(
            sender="PolicyAgent",
            receiver="DataAgent",
            type="POLICY",
            payload={"policy": policy},
            session_id=msg.session_id,
        )
        bus.send(out_msg)
        logger.info("PolicyAgent sent POLICY to DataAgent for session %s", msg.session_id)

    def _generate_policy(self, text: str, region_id: str) -> Dict[str, Any]:
        """
        Very simple heuristic parser that extracts:
        - time_horizon_years
        - co2_reduction_percent
        - optional job_loss_max_percent & budget_limit_usd

        Replace this logic with an actual LLM-based parser later.
        """
        # Defaults
        policy: Dict[str, Any] = {
            "region_id": region_id,
            "time_horizon_years": 10,
            "targets": {
                "co2_reduction_percent": 30,
                "job_loss_max_percent": 5,
                "budget_limit_usd": 500_000_000,
            },
            "constraints": [],
            "raw_text": text,
        }

        text_lower = text.lower()

        # crude extraction of horizon
        for years in (5, 10, 15, 20):
            if f"{years}-year" in text_lower or f"{years} year" in text_lower:
                policy["time_horizon_years"] = years
                break

        # crude extraction of % reduction
        for pct in (20, 30, 40, 50, 60):
            if f"{pct}%" in text_lower or f"{pct} percent" in text_lower:
                policy["targets"]["co2_reduction_percent"] = pct
                break

        # crude constraints examples
        if "no nuclear" in text_lower:
            policy["constraints"].append("no nuclear")
        if "protect wetlands" in text_lower:
            policy["constraints"].append("protect wetlands")

        logger.debug("PolicyAgent generated policy: %s", policy)
        return policy
