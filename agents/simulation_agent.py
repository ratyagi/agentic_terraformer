# Runs code-based environmental simulations
# Goal: Numerically simulate impact of each scenario.
import logging
from typing import Any, Dict

from core.models import AgentMessage
from tools.intervention_tool import load_interventions
from tools.simulation_tool import simulate_scenario

logger = logging.getLogger(__name__)


class SimulationAgent:
    """
    SimulationAgent

    Receives SCENARIO messages and performs numerical simulation to
    estimate emissions, cost, and job impact. Sends results to EvaluationAgent.
    """

    def __init__(self):
        # Preload interventions catalog to avoid re-reading file
        self.interventions_catalog = load_interventions()

    def handle_message(self, msg: AgentMessage, bus: "MessageBus") -> None:
        if msg.type != "SCENARIO":
            logger.debug("SimulationAgent ignoring message type %s", msg.type)
            return

        policy: Dict[str, Any] = msg.payload["policy"]
        region: Dict[str, Any] = msg.payload["region"]
        scenario: Dict[str, Any] = msg.payload["scenario"]

        scenario_id = scenario["scenario_id"]
        logger.info(
            "SimulationAgent simulating %s for region %s (session %s)",
            scenario_id,
            policy["region_id"],
            msg.session_id,
        )

        sim_result = simulate_scenario(region, scenario, self.interventions_catalog)

        out_payload = {
            "policy": policy,
            "region": region,
            "scenario": scenario,
            "simulation": sim_result,
        }

        out_msg = AgentMessage(
            sender="SimulationAgent",
            receiver="EvaluationAgent",
            type="SIM_RESULT",
            payload=out_payload,
            session_id=msg.session_id,
        )
        bus.send(out_msg)
        logger.info(
            "SimulationAgent sent SIM_RESULT for %s to EvaluationAgent (session %s)",
            scenario_id,
            msg.session_id,
        )
