# Generates final human-readable reports (LLM)
import logging
from typing import Any, Dict, List

from core.models import AgentMessage
from tools.storage_tool import save_report

logger = logging.getLogger(__name__)


class ReportAgent:
    """
    ReportAgent

    Converts evaluation summary into a human-readable report, and saves it
    via storage_tool. In a full version, it would use an LLM to write a
    polished narrative.
    """

    def handle_message(self, msg: AgentMessage, bus: "MessageBus") -> None:
        if msg.type != "EVAL_SUMMARY":
            logger.debug("ReportAgent ignoring message type %s", msg.type)
            return

        summary: Dict[str, Any] = msg.payload
        report = self._generate_report(summary)

        # Persist report
        save_report(msg.session_id, report)

        logger.info("ReportAgent saved report for session %s", msg.session_id)

        # Notify orchestrator that report is ready
        out_msg = AgentMessage(
            sender="ReportAgent",
            receiver="Orchestrator",
            type="REPORT_READY",
            payload={"report": report},
            session_id=msg.session_id,
        )
        bus.send(out_msg)
        logger.info("ReportAgent sent REPORT_READY to Orchestrator for session %s", msg.session_id)

    def _generate_report(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Turn best scenario + metrics into a simple structured report.
        """
        best = summary["best_scenario"]
        metrics = summary["metrics"]
        ranked: List[Dict[str, Any]] = summary["ranked_scenarios"]

        policy = best["policy"]
        region = best["region"]
        scenario = best["scenario"]
        sim = best["simulation"]

        title = f"Sustainability Plan for {region.get('name', policy['region_id'])}"

        executive_summary = (
            f"This plan reduces CO2 emissions by "
            f"{sim['co2_reduction_percent']:.1f}% over "
            f"{policy['time_horizon_years']} years for region "
            f"{region.get('name', policy['region_id'])}. "
            f"The projected total cost is ${sim['total_cost_usd']:,.0f}, "
            f"with an estimated jobs impact of "
            f"{sim.get('estimated_jobs_change_percent', 0.0):.1f}%."
        )

        actions_lines = []
        for a in scenario["actions"]:
            line = f"- Intervention {a['id']} at {a['scale']} scale"
            actions_lines.append(line)
        actions_text = "\n".join(actions_lines)

        body = (
            executive_summary
            + "\n\nKey Actions:\n"
            + actions_text
            + "\n\nAdditional Scenarios Evaluated:\n"
        )

        for entry in ranked:
            sc = entry["scenario"]
            ssim = entry["simulation"]
            body += (
                f"- {sc['scenario_id']}: "
                f"{ssim['co2_reduction_percent']:.1f}% reduction, "
                f"cost ${ssim['total_cost_usd']:,.0f}\n"
            )

        report = {
            "title": title,
            "executive_summary": executive_summary,
            "body": body,
            "best_scenario": best,
            "metrics": metrics,
        }

        return report
