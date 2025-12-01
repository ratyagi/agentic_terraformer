"""
main.py

Command-line entry point for Agentic Terraformer.

Runs a single end-to-end session with a hard-coded or user-provided goal,
and prints the final report summary.
"""

from __future__ import annotations

import argparse
import logging
from typing import Optional

from core.config import setup_logging, DEFAULT_REGION_ID
from core.message_bus import MessageBus
from core.models import AgentMessage
from core.session_manager import start_session, update_session_status
from tools.storage_tool import load_report
from tools.memory_tool import append_session_summary

from agents.orchestrator import Orchestrator
from agents.policy_agent import PolicyAgent
from agents.data_agent import DataAgent
from agents.scenario_agent import ScenarioAgent
from agents.simulation_agent import SimulationAgent
from agents.evaluation_agent import EvaluationAgent
from agents.report_agent import ReportAgent


logger = logging.getLogger(__name__)


def build_system() -> MessageBus:
    """
    Instantiate the MessageBus and register all agents.
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


def run_session(goal_text: str, region_id: Optional[str] = None) -> Optional[str]:
    """
    Create a session, run the agent pipeline, and return the session_id.
    """
    if region_id is None:
        region_id = DEFAULT_REGION_ID

    state = start_session(goal_text, region_id)
    session_id = state.session_id

    update_session_status(session_id, "running")

    bus = build_system()

    # Kick off the process with a START message to Orchestrator
    start_msg = AgentMessage(
        sender="User",
        receiver="Orchestrator",
        type="START",
        payload={
            "goal_text": goal_text,
            "region_id": region_id,
        },
        session_id=session_id,
    )
    bus.send(start_msg)

    # Run until the queue is empty
    bus.run(session_id=session_id)

    update_session_status(session_id, "completed")

    logger.info("Session %s completed", session_id)
    return session_id


def print_report(session_id: str) -> None:
    """
    Load the report for a session and print a short textual summary
    to stdout. Also update long-term memory.
    """
    report = load_report(session_id)
    if report is None:
        print(f"No report found for session {session_id}")
        return

    title = report.get("title", "Untitled Report")
    summary = report.get("executive_summary", "")
    best = report.get("best_scenario", {})

    score = float(best.get("score", 0.0))
    region_id = best.get("policy", {}).get("region_id", "unknown")
    sim = best.get("simulation", {})

    co2_red = float(sim.get("co2_reduction_percent", 0.0))
    total_cost = float(sim.get("total_cost_usd", 0.0))

    # Update long-term memory
    append_session_summary(
        session_id=session_id,
        region_id=region_id,
        co2_reduction_percent=co2_red,
        total_cost_usd=total_cost,
        score=score,
    )

    print("=" * 80)
    print(title)
    print("=" * 80)
    print(summary)
    print("\nBest Scenario Score:", f"{score:.2f}")
    print("CO2 Reduction (%):", f"{co2_red:.2f}")
    print("Total Cost (USD):", f"{total_cost:,.0f}")
    print("=" * 80)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Agentic Terraformer session.")
    parser.add_argument(
        "--goal",
        type=str,
        default=(
            "Design a 10-year plan to reduce CO2 emissions by 40% in coastal_city_01 "
            "with minimal job loss."
        ),
        help="Natural language sustainability goal text.",
    )
    parser.add_argument(
        "--region",
        type=str,
        default=DEFAULT_REGION_ID,
        help="Region ID to apply the goal to.",
    )
    return parser.parse_args()


def main() -> None:
    setup_logging()
    args = parse_args()

    logger.info("Starting Agentic Terraformer main run")
    session_id = run_session(args.goal, args.region)

    if session_id:
        print_report(session_id)


if __name__ == "__main__":
    main()
