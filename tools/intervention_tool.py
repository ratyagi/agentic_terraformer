# Catalog of interventions & effects
"""
tools.intervention_tool

Utility functions for loading the catalog of possible interventions.
"""

import csv
import logging
from typing import Dict

from core.config import DATA_DIR

logger = logging.getLogger(__name__)

INTERVENTIONS_FILE = DATA_DIR / "interventions.csv"


def _ensure_sample_interventions_file() -> None:
    """
    If interventions.csv does not exist OR is empty, create a small sample file so the
    system can run without manual setup.
    """
    if INTERVENTIONS_FILE.exists() and INTERVENTIONS_FILE.stat().st_size > 0:
        return

    logger.warning(
        "interventions.csv missing or empty, creating a sample file at %s",
        INTERVENTIONS_FILE,
    )

    sample_rows = [
        {
            "id": "EV_SUBSIDY",
            "name": "EV subsidies",
            "sector": "transport",
            "base_reduction_percent_per_unit": "5.0",
            "base_cost_usd_per_unit": "100000000",
            "job_impact_percent_per_unit": "-0.2",
        },
        {
            "id": "PUBLIC_TRANSIT_EXPANSION",
            "name": "Public transit expansion",
            "sector": "transport",
            "base_reduction_percent_per_unit": "8.0",
            "base_cost_usd_per_unit": "200000000",
            "job_impact_percent_per_unit": "0.5",
        },
        {
            "id": "BUILDING_RETROFIT",
            "name": "Building retrofits",
            "sector": "buildings",
            "base_reduction_percent_per_unit": "10.0",
            "base_cost_usd_per_unit": "250000000",
            "job_impact_percent_per_unit": "0.1",
        },
        {
            "id": "INDUSTRIAL_EFFICIENCY",
            "name": "Industrial efficiency upgrades",
            "sector": "industry",
            "base_reduction_percent_per_unit": "7.0",
            "base_cost_usd_per_unit": "180000000",
            "job_impact_percent_per_unit": "0.2",
        },
    ]

    fieldnames = list(sample_rows[0].keys())
    INTERVENTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with INTERVENTIONS_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sample_rows:
            writer.writerow(row)


def _convert_intervention_row(row: Dict[str, str]) -> Dict:
    """
    Convert CSV strings to numeric types and normalized structure.
    """
    def _float(name: str, default: float = 0.0) -> float:
        try:
            return float(row.get(name, default))
        except ValueError:
            return default

    iv = {
        "id": row.get("id"),
        "name": row.get("name"),
        "sector": row.get("sector"),
        "base_reduction_percent_per_unit": _float("base_reduction_percent_per_unit"),
        "base_cost_usd_per_unit": _float("base_cost_usd_per_unit"),
        "job_impact_percent_per_unit": _float("job_impact_percent_per_unit"),
    }
    return iv


def load_interventions() -> Dict[str, Dict]:
    """
    Load interventions from interventions.csv as a mapping from id -> dict.
    """
    _ensure_sample_interventions_file()

    catalog: Dict[str, Dict] = {}
    with INTERVENTIONS_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            iv_id = row["id"]
            catalog[iv_id] = _convert_intervention_row(row)

    logger.info("Loaded %d interventions from %s", len(catalog), INTERVENTIONS_FILE)
    return catalog
