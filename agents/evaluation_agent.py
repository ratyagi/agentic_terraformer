# Scores scenarios
# Goal: Score scenarios and decide which are viable.
import logging
from typing import Any, Dict, List, Tuple

from core.models import AgentMessage

logger = logging.getLogger(__name__)


class EvaluationAgent:
    """
    EvaluationAgent

    Aggregates simulation results, computes scores for each scenario based on
    policy targets and constraints, and selects the best scenario. Sends summary
    to ReportAgent.
    """

    def __init__(self):
        # session_id -> dict with expected_count, results list
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def handle_message(self, msg: AgentMessage, bus: "MessageBus") -> None:
        if msg.type == "SCENARIO_COUNT":
            self._handle_scenario_count(msg)
        elif msg.type == "SIM_RESULT":
            self._handle_sim_result(msg, bus)
        else:
            logger.debug("EvaluationAgent ignoring message type %s", msg.type)

    def _handle_scenario_count(self, msg: AgentMessage) -> None:
        expected = int(msg.payload["count"])
        session_id = msg.session_id
        if session_id not in self._sessions:
            self._sessions[session_id] = {"expected": expected, "results": []}
        else:
            self._sessions[session_id]["expected"] = expected

        logger.info(
            "EvaluationAgent expecting %d scenarios for session %s",
            expected,
            session_id,
        )

    def _handle_sim_result(self, msg: AgentMessage, bus: "MessageBus") -> None:
        session_id = msg.session_id
        if session_id not in self._sessions:
            self._sessions[session_id] = {"expected": None, "results": []}

        self._sessions[session_id]["results"].append(msg.payload)

        expected = self._sessions[session_id].get("expected")
        results = self._sessions[session_id]["results"]

        logger.info(
            "EvaluationAgent received SIM_RESULT (%d/%s expected) for session %s",
            len(results),
            expected,
            session_id,
        )

        if expected is not None and len(results) >= expected:
            logger.info("EvaluationAgent has all results for session %s; evaluating", session_id)
            summary = self._evaluate_session(results)
            out_msg = AgentMessage(
                sender="EvaluationAgent",
                receiver="ReportAgent",
                type="EVAL_SUMMARY",
                payload=summary,
                session_id=session_id,
            )
            bus.send(out_msg)
            # Optionally clear session to save memory
            del self._sessions[session_id]

    def _evaluate_session(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute a score for each scenario and pick the best one.
        """
        scored: List[Tuple[float, Dict[str, Any]]] = []

        for entry in results:
            policy = entry["policy"]
            simulation = entry["simulation"]
            scenario = entry["scenario"]

            score = self._score_scenario(policy, simulation)
            scored.append((score, entry))

            logger.debug(
                "Scenario %s has score %.2f (sim=%s)",
                scenario["scenario_id"],
                score,
                simulation,
            )

        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_entry = scored[0]

        # Aggregate metrics
        co2_reductions = [e["simulation"]["co2_reduction_percent"] for _, e in scored]
        costs = [e["simulation"]["total_cost_usd"] for _, e in scored]

        summary = {
            "best_scenario": {
                "score": best_score,
                "policy": best_entry["policy"],
                "region": best_entry["region"],
                "scenario": best_entry["scenario"],
                "simulation": best_entry["simulation"],
            },
            "ranked_scenarios": [
                {
                    "score": s,
                    "scenario": e["scenario"],
                    "simulation": e["simulation"],
                }
                for s, e in scored
            ],
            "metrics": {
                "num_scenarios": len(scored),
                "avg_co2_reduction_percent": sum(co2_reductions) / len(co2_reductions),
                "avg_total_cost_usd": sum(costs) / len(costs),
                "max_co2_reduction_percent": max(co2_reductions),
                "min_total_cost_usd": min(costs),
            },
        }

        logger.info(
            "EvaluationAgent selected best scenario %s with score %.2f",
            summary["best_scenario"]["scenario"]["scenario_id"],
            best_score,
        )
        return summary

    def _score_scenario(self, policy: Dict[str, Any], sim: Dict[str, Any]) -> float:
        """
        Simple scoring function:

        score = w1 * reduction - w2 * budget_overshoot - w3 * jobs_penalty

        All weights are hand-tuned placeholders you can adjust.
        """
        targets = policy["targets"]
        target_reduction = targets["co2_reduction_percent"]
        reduction = sim["co2_reduction_percent"]

        # reward getting close to or above target
        reduction_score = reduction - max(0.0, target_reduction - reduction)

        budget_limit = targets.get("budget_limit_usd")
        cost = sim["total_cost_usd"]
        if budget_limit is not None and cost > budget_limit:
            budget_overshoot = (cost - budget_limit) / max(budget_limit, 1.0)
        else:
            budget_overshoot = 0.0

        job_limit = targets.get("job_loss_max_percent", 5)
        jobs_change = sim.get("estimated_jobs_change_percent", 0.0)
        jobs_penalty = 0.0
        if jobs_change < -job_limit:
            jobs_penalty = abs(jobs_change) - job_limit

        # weights
        w1 = 1.0
        w2 = 50.0
        w3 = 10.0

        score = w1 * reduction_score - w2 * budget_overshoot - w3 * jobs_penalty
        return score
