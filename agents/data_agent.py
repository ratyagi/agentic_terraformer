 # Loads regional data
# Goal: Fetch baseline regional data and context.
import logging
from typing import Any, Dict

from core.models import AgentMessage
from tools.climate_data_tool import load_region

logger = logging.getLogger(__name__)


class DataAgent:
    """
    DataAgent

    Given a POLICY, loads regional baseline data and forwards both
    to the ScenarioAgent.
    """

    def handle_message(self, msg: AgentMessage, bus: "MessageBus") -> None:
        if msg.type != "POLICY":
            logger.debug("DataAgent ignoring message type %s", msg.type)
            return

        policy: Dict[str, Any] = msg.payload["policy"]
        region_id = policy["region_id"]

        logger.info("DataAgent loading data for region %s (session %s)", region_id, msg.session_id)

        region_data = load_region(region_id)

        payload = {
            "policy": policy,
            "region": region_data,
        }

        out_msg = AgentMessage(
            sender="DataAgent",
            receiver="ScenarioAgent",
            type="REGION_CONTEXT",
            payload=payload,
            session_id=msg.session_id,
        )
        bus.send(out_msg)
        logger.info("DataAgent sent REGION_CONTEXT to ScenarioAgent for session %s", msg.session_id)
