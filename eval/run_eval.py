# Script: runs multiple scenarios, computes metrics
"""
eval.run_eval

Offline evaluation script for Agentic Terraformer.

Compares the multi-agent system against a simple baseline heuristic
on a small set of test goals defined in eval/scenarios.json.

Run via:
    python -m eval.run_eval
or from the repo root:
    python eval/run_eval.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure project root is on sys.path when executed as script
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.config import setup_logging, DEFAULT_REGION_ID  # type: ignore  # noqa: E402
from core.message_bus import MessageBus  # type: ignore  # noqa: E402
from core.models import AgentMessage  # type: ignore  # noqa: E402
from core.session_manager import start_session, update_session_status  # type: ignore  # noqa: E402

from tools.storage_tool import load_report  # type: ignore  # noqa: E402
from tools.climate_data_tool import load_region  # type: ignore  # noqa: E402
from tools.intervention_tool import load_interventions  # type: ignore  # noqa: E402
from tools.simulation_tool import simulate_scenario  # type: ignore  # noqa: E402

from agents.orchestrator import Orchestrator  # type: ignore  # noqa: E402
from agents.policy_agent import PolicyAgent  # type: ignore  # noqa: E402
from agents.data_agent import DataAgent  # type: ignore  # noqa: E402
from agents.scenario_agent import ScenarioAgent  # type: ignore  # noqa: E402
from agents.simulation_agent import SimulationAgent  # type: ignore  # noqa: E402
from agents.evaluation_agent import EvaluationAgent  # type: ignore  # noqa: E402
from agents.report_agent import ReportAgent  # type: ignore  # noqa: E402


logger = logging.getLogger(__name__)

EVAL_DIR = ROOT_DIR / "eval"
SCENARIOS_FILE = EVAL_DIR / "scenarios.json"
RESULTS_FILE = EVAL_DIR / "results.json"


def _ensure_sample_scenarios() -> None:
    """
    If eval/scenarios.json doesn't exist, create a small sample set.
    """
    if SCENARIOS_FILE.exists():
        return

    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    sample = [
        {
            "name": "Dense Coastal City Aggressive Target",
            "region_id": "coastal_city_01",
            "goal": (
                "Reduce CO2 emissions by 50% in 10 years for coastal_city_01 "
                "while limiting job losses to 3%."
            ),
        },
        {
            "name": "Industrial Region Moderate Target",
            "region_id": "industrial_region_02",
            "goal": (
                "Reduce CO2 emissions by 25% in 5 years for industrial_region_02 "
                "with minimal budget and no major job losses."
            ),
        },
    ]

    with SCENARIOS_FILE.open("w", encoding="utf-8") as f:
        json.dump(sample, f, indent=2)

    logger.warning("Created sample evaluation scenarios at %s", SCENARIOS_FILE)


def build_system() -> MessageBus:
    """
    Build a fresh MessageBus with all agents registered.
    """
    bus = MessageBus()

    orchestrator = Orchestrator()
    policy_agent = PolicyAgent(default_region_id=DEFAULT_REGION_ID)
    data_agent = DataAgent()
    scenario_agent = ScenarioAgent()
    simulation_agent = SimulationAgent()
    evaluation_agent = EvaluationAgent()
    report_agent = ReportAgent()

    bus.register_agent("Orchestrator", orchestrator)
    bus.register_agent("PolicyAgent", policy_agent)
    bus.register_agent("DataAgent", data_agent)
    bus.register_agent("ScenarioAgent", scenario_agent)
    bus.register_agent("SimulationAgent", simulation_agent)
    bus.register_agent("EvaluationAgent", evaluation_agent)
    bus.register_agent("ReportAgent", report_agent)

    return bus


def run_agentic(goal_text: str, region_id: str) -> float:
    """
    Run the full multi-agent pipeline for a given goal and region.
    Returns the best scenario score from the report.
    """
    state = start_session(goal_text, region_id)
    session_id = state.session_id

    update_session_status(session_id, "running")

    bus = build_system()

    start_msg = AgentMessage(
        sender="Eval",
        receiver="Orchestrator",
        type="START",
        payload={"goal_text": goal_text, "region_id": region_id},
        session_id=session_id,
    )
    bus.send(start_msg)
    bus.run(session_id=session_id)

    update_session_status(session_id, "completed")

    report = load_report(session_id)
    if report is None:
        logger.error("No report generated for session %s", session_id)
        return 0.0

    best = report.get("best_scenario", {})
    score = float(best.get("score", 0.0))
    return score


def baseline_scenario(region_id: str) -> Tuple[float, Dict[str, Any]]:
    """
    Simple baseline heuristic:

    - For the given region, build a static scenario using the cheapest
      interventions in each sector (low scale).
    - Simulate and score it using the same scoring logic as EvaluationAgent.

    Returns:
        (score, simulation_result_dict)
    """
    region = load_region(region_id)
    interventions = load_interventions()

    # Choose cheapest intervention per sector
    by_sector: Dict[str, Dict[str, Any]] = {}
    for iv in interventions.values():
        sector = iv["sector"]
        if sector not in by_sector or iv["base_cost_usd_per_unit"] < by_sector[sector][
            "base_cost_usd_per_unit"
        ]:
            by_sector[sector] = iv

    actions: List[Dict[str, Any]] = []
    for iv in by_sector.values():
        actions.append({"id": iv["id"], "scale": "low"})

    scenario = {
        "scenario_id": "BASELINE",
        "actions": actions,
    }

    sim = simulate_scenario(region, scenario, interventions)

    # Dummy target policy for scoring (moderate target)
    policy = {
        "region_id": region_id,
        "time_horizon_years": 10,
        "targets": {
            "co2_reduction_percent": 30,
            "job_loss_max_percent": 5,
            "budget_limit_usd": 500_000_000,
        },
    }

    score = _score_scenario(policy, sim)
    return score, sim


def _score_scenario(policy: Dict[str, Any], sim: Dict[str, Any]) -> float:
    """
    Same scoring design as EvaluationAgent._score_scenario.
    """
    targets = policy["targets"]
    target_reduction = targets["co2_reduction_percent"]
    reduction = sim["co2_reduction_percent"]

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

    w1 = 1.0
    w2 = 50.0
    w3 = 10.0

    score = w1 * reduction_score - w2 * budget_overshoot - w3 * jobs_penalty
    return score


def run_evaluation() -> None:
    """
    Load scenarios, run both baseline and agentic systems, and save results.
    """
    _ensure_sample_scenarios()

    with SCENARIOS_FILE.open("r", encoding="utf-8") as f:
        scenarios = json.load(f)

    results: List[Dict[str, Any]] = []

    for sc in scenarios:
        name = sc["name"]
        region_id = sc.get("region_id", DEFAULT_REGION_ID)
        goal = sc["goal"]

        logger.info("Evaluating scenario: %s (%s)", name, region_id)

        base_score, base_sim = baseline_scenario(region_id)
        agentic_score = run_agentic(goal, region_id)

        result = {
            "name": name,
            "region_id": region_id,
            "goal": goal,
            "baseline": {
                "score": base_score,
                "simulation": base_sim,
            },
            "agentic": {
                "score": agentic_score,
            },
            "agentic_better": agentic_score > base_score,
        }

        results.append(result)

    summary = _summarize_results(results)

    payload = {
        "results": results,
        "summary": summary,
    }

    with RESULTS_FILE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info("Saved evaluation results to %s", RESULTS_FILE)

    # Print brief summary to stdout
    print("=== Evaluation Summary ===")
    print(json.dumps(summary, indent=2))


def _summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not results:
        return {
            "num_cases": 0,
            "agentic_wins": 0,
            "baseline_wins": 0,
            "ties": 0,
        }

    agentic_wins = 0
    baseline_wins = 0
    ties = 0

    for r in results:
        b = r["baseline"]["score"]
        a = r["agentic"]["score"]
        if a > b:
            agentic_wins += 1
        elif b > a:
            baseline_wins += 1
        else:
            ties += 1

    return {
        "num_cases": len(results),
        "agentic_wins": agentic_wins,
        "baseline_wins": baseline_wins,
        "ties": ties,
    }


def main() -> None:
    setup_logging()
    logger.info("Starting Agentic Terraformer evaluation")
    run_evaluation()


if __name__ == "__main__":
    main()
