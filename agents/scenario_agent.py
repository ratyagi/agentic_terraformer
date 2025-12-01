# Proposes intervention scenarios (LLM)
# Goal: Propose multiple intervention portfolios (parallelizable).
import logging
import random
from typing import Any, Dict, List

from core.models import AgentMessage
from tools.intervention_tool import load_interventions

logger = logging.getLogger(__name__)


class ScenarioAgent:
    """
    ScenarioAgent

    Given region context + policy, proposes a set of candidate scenarios
    (portfolios of interventions) and sends them for simulation.
    """

    def __init__(self, num_scenarios: int = 3, min_actions: int = 2, max_actions: int = 4):
        self.num_scenarios = num_scenarios
        self.min_actions = min_actions
        self.max_actions = max_actions

    def handle_message(self, msg: AgentMessage, bus: "MessageBus") -> None:
        if msg.type != "REGION_CONTEXT":
            logger.debug("ScenarioAgent ignoring message type %s", msg.type)
            return

        policy: Dict[str, Any] = msg.payload["policy"]
        region: Dict[str, Any] = msg.payload["region"]

        logger.info(
            "ScenarioAgent generating scenarios for region %s (session %s)",
            policy["region_id"],
            msg.session_id,
        )

        interventions_catalog = load_interventions()
        scenarios = self._generate_scenarios(policy, region, interventions_catalog)

        if not scenarios:
            logger.error("ScenarioAgent could not generate any scenarios (no interventions available).")
            # You could notify ReportAgent here with a failure, but for now we just stop.
            return

        # Inform EvaluationAgent how many scenarios to expect
        count_msg = AgentMessage(
            sender="ScenarioAgent",
            receiver="EvaluationAgent",
            type="SCENARIO_COUNT",
            payload={"count": len(scenarios)},
            session_id=msg.session_id,
        )
        bus.send(count_msg)

        for scenario in scenarios:
            out_payload = {
                "policy": policy,
                "region": region,
                "scenario": scenario,
                "intervention_ids": [a["id"] for a in scenario["actions"]],
            }
            out_msg = AgentMessage(
                sender="ScenarioAgent",
                receiver="SimulationAgent",
                type="SCENARIO",
                payload=out_payload,
                session_id=msg.session_id,
            )
            bus.send(out_msg)
            logger.info(
                "ScenarioAgent sent SCENARIO %s to SimulationAgent (session %s)",
                scenario["scenario_id"],
                msg.session_id,
            )

    def _generate_scenarios(
        self,
        policy: Dict[str, Any],
        region: Dict[str, Any],
        interventions_catalog: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Simple scenario generator: randomly sample intervention combinations.
        """
        all_ids = list(interventions_catalog.keys())
        random.shuffle(all_ids)

        if not all_ids:
            logger.error("No interventions available to generate scenarios.")
            return []

        # Clamp min/max based on available interventions
        max_actions_available = max(1, min(self.max_actions, len(all_ids)))
        min_actions = min(self.min_actions, max_actions_available)

        scenarios: List[Dict[str, Any]] = []
        for i in range(self.num_scenarios):
            num_actions = random.randint(min_actions, max_actions_available)
            chosen_ids = random.sample(all_ids, num_actions)

            actions = []
            for iv_id in chosen_ids:
                scale = random.choice(["low", "medium", "high"])
                actions.append({"id": iv_id, "scale": scale})

            scenario = {
                "scenario_id": f"S{i+1}",
                "actions": actions,
            }
            scenarios.append(scenario)

        logger.debug("ScenarioAgent generated scenarios: %s", scenarios)
        return scenarios

