# Script: runs multiple scenarios, computes metrics
"""
ui.app_streamlit

Streamlit UI for Agentic Terraformer.

Run via:
    streamlit run ui/app_streamlit.py
"""

from __future__ import annotations

import logging

import streamlit as st

from core.config import setup_logging, DEFAULT_REGION_ID
from core.message_bus import MessageBus
from core.models import AgentMessage
from core.session_manager import start_session, update_session_status
from tools.storage_tool import load_report
from tools.memory_tool import summarize_patterns

from agents.orchestrator import Orchestrator
from agents.policy_agent import PolicyAgent
from agents.data_agent import DataAgent
from agents.scenario_agent import ScenarioAgent
from agents.simulation_agent import SimulationAgent
from agents.evaluation_agent import EvaluationAgent
from agents.report_agent import ReportAgent


# Ensure logging is configured once
setup_logging()
logger = logging.getLogger(__name__)


def build_system() -> MessageBus:
    """
    Build a fresh MessageBus with registered agents.
    Called per-run for simplicity; overhead is small.
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


def run_agentic_terraformer(goal_text: str, region_id: str) -> str:
    """
    Create a session, run the agent pipeline, return session_id.
    """
    state = start_session(goal_text, region_id)
    session_id = state.session_id

    update_session_status(session_id, "running")

    bus = build_system()

    start_msg = AgentMessage(
        sender="UI",
        receiver="Orchestrator",
        type="START",
        payload={
            "goal_text": goal_text,
            "region_id": region_id,
        },
        session_id=session_id,
    )
    bus.send(start_msg)
    bus.run(session_id=session_id)

    update_session_status(session_id, "completed")

    logger.info("UI completed session %s", session_id)
    return session_id


def main() -> None:
    st.set_page_config(
        page_title="Agentic Terraformer",
        page_icon="🌍",
        layout="wide",
    )

    st.title("🌍 Agentic Terraformer")
    st.markdown(
        "A multi-agent system that designs, simulates, and evaluates sustainability plans."
    )

    with st.sidebar:
        st.header("Run Configuration")
        region_id = st.text_input(
            "Region ID",
            value=DEFAULT_REGION_ID,
            help="Pick a region ID defined in data/regions.csv",
        )
        default_goal = (
            "Design a 10-year plan to reduce CO2 emissions by 40% in "
            f"{region_id} with minimal job loss."
        )

    st.subheader("Define Your Sustainability Goal")
    goal_text = st.text_area(
        "Goal description",
        value=default_goal,
        height=150,
        help="Describe the sustainability target in natural language.",
    )

    run_button = st.button("Run Agentic Terraformer 🚀")

    col1, col2 = st.columns([2, 1])

    if run_button and goal_text.strip():
        with st.spinner("Running multi-agent pipeline..."):
            session_id = run_agentic_terraformer(goal_text.strip(), region_id.strip())

        with col1:
            st.subheader("Resulting Plan")
            report = load_report(session_id)
            if report is None:
                st.error("No report generated.")
            else:
                st.markdown(f"**Session ID:** `{session_id}`")
                st.markdown(f"### {report.get('title', 'Untitled Plan')}")
                st.write(report.get("executive_summary", ""))

                st.markdown("#### Detailed Report")
                st.text(report.get("body", ""))

                best = report.get("best_scenario", {})
                sim = best.get("simulation", {})
                st.markdown("#### Key Metrics")
                st.json(
                    {
                        "score": best.get("score", 0.0),
                        "co2_reduction_percent": sim.get("co2_reduction_percent", 0.0),
                        "total_cost_usd": sim.get("total_cost_usd", 0.0),
                        "estimated_jobs_change_percent": sim.get(
                            "estimated_jobs_change_percent", 0.0
                        ),
                    }
                )

        with col2:
            st.subheader("Long-Term Memory Summary")
            summary = summarize_patterns()
            st.json(summary)

    elif not run_button:
        with col2:
            st.subheader("Long-Term Memory Summary")
            summary = summarize_patterns()
            st.json(summary)


if __name__ == "__main__":
    main()
