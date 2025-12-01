# Reads climate/regional data
"""
tools.climate_data_tool

Utility functions for loading regional climate / baseline data.
"""

import csv
import logging
from pathlib import Path
from typing import Dict

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


def _convert_region_row(row: Dict[str, str]) -> Dict:
    """
    Convert CSV strings to appropriate numeric types.
    """
    try:
        population = int(row.get("population", "0"))
    except ValueError:
        population = 0

    def _float(name: str, default: float = 0.0) -> float:
        try:
            return float(row.get(name, default))
        except ValueError:
            return default

    region = {
        "region_id": row.get("region_id"),
        "name": row.get("name"),
        "population": population,
        "current_emissions_mtco2": _float("current_emissions_mtco2"),
        "sector_breakdown": {
            "transport": _float("transport_share"),
            "industry": _float("industry_share"),
            "buildings": _float("buildings_share"),
        },
    }
    return region


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


def load_region(region_id: str) -> Dict:
    """
    Load a single region by id. Raises KeyError if not found.
    """
    regions = load_all_regions()
    if region_id not in regions:
        available = ", ".join(regions.keys())
        msg = f"Region '{region_id}' not found. Available: {available}"
        logger.error(msg)
        raise KeyError(msg)

    logger.debug("Loaded region %s", region_id)
    return regions[region_id]
