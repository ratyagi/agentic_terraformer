# Reads climate/regional data
"""
tools.climate_data_tool

Utility functions for loading regional climate / baseline data.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List

from core.config import DATA_DIR

logger = logging.getLogger(__name__)

REGIONS_FILE = DATA_DIR / "regions.csv"


def _ensure_sample_regions_file() -> None:
    """
    If regions.csv does not exist, create a small sample file so the
    system can run end-to-end without manual setup.
    """
    if REGIONS_FILE.exists():
        return

    logger.warning("regions.csv not found, creating a sample file at %s", REGIONS_FILE)

    sample_rows = [
        {
            "region_id": "coastal_city_01",
            "name": "Coastal City",
            "population": "2500000",
            "current_emissions_mtco2": "15.0",
            "transport_share": "0.4",
            "industry_share": "0.3",
            "buildings_share": "0.3",
        },
        {
            "region_id": "industrial_region_02",
            "name": "Industrial Region",
            "population": "1800000",
            "current_emissions_mtco2": "22.0",
            "transport_share": "0.25",
            "industry_share": "0.55",
            "buildings_share": "0.20",
        },
    ]

    fieldnames = list(sample_rows[0].keys())
    REGIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with REGIONS_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sample_rows:
            writer.writerow(row)


def load_all_regions() -> Dict[str, Dict]:
    """
    Load all regions from regions.csv as a mapping from region_id to dict.
    """
    _ensure_sample_regions_file()

    regions: Dict[str, Dict] = {}
    with REGIONS_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            region_id = row["region_id"]
            regions[region_id] = _convert_region_row(row)

    logger.info("Loaded %d regions from %s", len(regions), REGIONS_FILE)
    return regions


def _convert_region_row(row: Dict[str, str]) -> Dict:
    """
    Convert CSV strings to appropriate numeric types.
    """
    try:
        population = int(row.get("population", "0"))
    except ValueError:
