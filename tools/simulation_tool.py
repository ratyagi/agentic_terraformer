# Numeric simulation utilities
"""
tools.simulation_tool

Core numerical simulation of scenarios:
Given a region, a scenario (portfolio of interventions), and the
interventions catalog, estimate emissions, cost, and job impact.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


SCALE_FACTORS = {
    "low": 0.5,
    "medium": 1.0,
    "high": 1.5,
}


def simulate_scenario(
    region: Dict,
    scenario: Dict,
    interventions_catalog: Dict[str, Dict],
) -> Dict:
    """
    Compute a simple, interpretable projection for a scenario.

    Args:
        region: dict with keys like "current_emissions_mtco2".
        scenario: dict with "scenario_id" and "actions" list.
        interventions_catalog: mapping from intervention id -> dict.

    Returns:
        dict with baseline_emissions, projected_emissions_mtco2,
        co2_reduction_percent, total_cost_usd, estimated_jobs_change_percent.
    """
    baseline = float(region.get("current_emissions_mtco2", 0.0))
    if baseline <= 0:
        logger.warning(
            "Region %s has non-positive baseline emissions, using 1.0",
            region.get("region_id"),
        )
        baseline = 1.0

    total_reduction = 0.0
    total_cost = 0.0
    jobs_impact = 0.0

    actions: List[Dict] = scenario.get("actions", [])

    for action in actions:
        iv_id = action.get("id")
        scale_label = action.get("scale", "medium")

        iv = interventions_catalog.get(iv_id)
        if iv is None:
            logger.warning("Unknown intervention id '%s' in scenario %s", iv_id, scenario.get("scenario_id"))
            continue

        scale_factor = SCALE_FACTORS.get(scale_label, 1.0)

        base_reduction_pct = iv["base_reduction_percent_per_unit"]  # per "unit"
        base_cost = iv["base_cost_usd_per_unit"]
        base_job_impact = iv["job_impact_percent_per_unit"]

        # Simple model: percent * scale_factor * baseline
        reduction_amount = base_reduction_pct * scale_factor * baseline / 100.0
        total_reduction += reduction_amount

        cost_amount = base_cost * scale_factor
        total_cost += cost_amount

        jobs_impact += base_job_impact * scale_factor

    new_emissions = max(baseline - total_reduction, 0.0)
    co2_reduction_percent = (baseline - new_emissions) / baseline * 100.0

    result = {
        "baseline_emissions": baseline,
        "projected_emissions_mtco2": new_emissions,
        "co2_reduction_percent": co2_reduction_percent,
        "total_cost_usd": total_cost,
        "estimated_jobs_change_percent": jobs_impact,
    }

    logger.debug(
        "Simulated scenario %s: %s",
        scenario.get("scenario_id"),
        result,
    )
    return result
