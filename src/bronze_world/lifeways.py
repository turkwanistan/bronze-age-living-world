from __future__ import annotations

from dataclasses import dataclass
from typing import Any

YEAR_DAYS = 360

# This is an explicit simulation calendar, not a reconstruction of exact Ugaritic
# month/day correspondences. The phase ordering follows Mediterranean dry-farming
# constraints described in the project encyclopedia; exact boundaries are fixture
# calibration under ASM-FIXTURE-008.
SEASONAL_PHASES: tuple[dict[str, Any], ...] = (
    {
        "start": 0,
        "end": 59,
        "phase": "wet_winter_growth",
        "agricultural_intensity": 0.55,
        "farm_activity": "winter crop tending, livestock care, maintenance, household craft",
        "pressures": ["weather exposure", "animal care", "stored-food management"],
    },
    {
        "start": 60,
        "end": 119,
        "phase": "spring_growth_and_weeding",
        "agricultural_intensity": 0.80,
        "farm_activity": "weeding, field guarding, livestock births, harvest preparation",
        "pressures": ["labor coordination", "field access", "livestock care"],
    },
    {
        "start": 120,
        "end": 179,
        "phase": "cereal_harvest_and_threshing",
        "agricultural_intensity": 1.00,
        "farm_activity": "cereal harvest, transport, threshing, storage",
        "pressures": ["harvest labor bottleneck", "storage", "transport"],
    },
    {
        "start": 180,
        "end": 239,
        "phase": "dry_summer_storage_and_vines",
        "agricultural_intensity": 0.68,
        "farm_activity": "threshing/storage completion, vine work, dry-season maintenance",
        "pressures": ["water access", "storage loss", "transport"],
    },
    {
        "start": 240,
        "end": 299,
        "phase": "grape_olive_and_field_preparation",
        "agricultural_intensity": 0.88,
        "farm_activity": "grape/olive work, processing, field preparation",
        "pressures": ["processing labor", "household storage", "field preparation"],
    },
    {
        "start": 300,
        "end": 359,
        "phase": "early_rains_and_sowing",
        "agricultural_intensity": 0.98,
        "farm_activity": "plowing, sowing, early-rain field work",
        "pressures": ["sowing window", "draft labor", "weather timing"],
    },
)

ROLE_ACTIVITY: dict[str, dict[str, Any]] = {
    "farmer": {"domain": "agriculture", "activity": "seasonal field and household agricultural work"},
    "dependent_field_worker": {"domain": "agriculture", "activity": "seasonal field labor under household/dependent obligations"},
    "textile_worker": {"domain": "textile", "activity": "fiber preparation, spinning, weaving, finishing"},
    "metal_craft_worker": {"domain": "metalcraft", "activity": "repair, recycling, fuel preparation, casting/finishing"},
    "craft_apprentice": {"domain": "metalcraft", "activity": "workshop assistance, hauling, tool/mold preparation, supervised finishing"},
    "recognized_craft_worker": {"domain": "metalcraft", "activity": "recognized workshop production, supervised responsibility and finishing"},
    "merchant": {"domain": "commerce", "activity": "credit, counterparties, weights/seals, cargo and route decisions"},
    "broker": {"domain": "commerce", "activity": "connect buyers/sellers, assess trust, information and terms"},
    "merchant_account_partner": {"domain": "commerce", "activity": "household trade accounts, reserves, counterpart obligations"},
    "market_trader": {"domain": "commerce", "activity": "local exchange, prices, customer ties, voyage-income smoothing"},
    "sailor": {"domain": "maritime", "activity": "vessel preparation, cargo handling, crew work, harbor/weather intelligence"},
    "porter": {"domain": "labor", "activity": "human portage for household, market, workshop or harbor"},
    "seasonal_worker": {"domain": "labor", "activity": "short-term labor where household and seasonal demand permit"},
    "scribe": {"domain": "scribal", "activity": "records, accounting, contracts, correspondence"},
    "interpreter": {"domain": "scribal", "activity": "language mediation for trade, administration and foreign contact"},
    "ritual_specialist": {"domain": "ritual", "activity": "household/community rites, offerings, consultation and ritual diagnosis"},
    "ritual_assistant": {"domain": "ritual", "activity": "prepare offerings/materials and assist household/community rites"},
    "healer_helper": {"domain": "care", "activity": "patient care, practical remedies and ritual-medical assistance"},
    "household_manager": {"domain": "household", "activity": "stores, care, labor allocation, property and household obligations"},
    "dependent_household_worker": {"domain": "household", "activity": "food processing, textile/care work and assigned household labor"},
    "corvee_laborer": {"domain": "institutional_labor", "activity": "labor owed or requested through palace/estate institutions"},
    "property_claimant": {"domain": "household", "activity": "property defense, household representation and kin negotiation"},
}


def calendar_context(day: int, *, start_day_of_year: int = 120) -> dict[str, Any]:
    """Return research-constrained seasonal context for one simulation day.

    ``start_day_of_year`` is deliberately scenario-configurable because the project does
    not claim an exact Ugaritic calendar date for simulation day 0. The default places
    the first micro-world slice in a cereal-harvest bottleneck so labor conflicts can be
    exercised without compressing an annual cycle.
    """
    doy = (int(start_day_of_year) + int(day)) % YEAR_DAYS
    phase = next(p for p in SEASONAL_PHASES if p["start"] <= doy <= p["end"])
    return {
        "day_of_year": doy,
        "phase": phase["phase"],
        "agricultural_intensity": phase["agricultural_intensity"],
        "farm_activity": phase["farm_activity"],
        "pressures": list(phase["pressures"]),
        "calendar_notice": (
            "Season ordering is research-constrained Mediterranean dry-farming; exact "
            "360-day alignment and simulation-day offset are ASM-FIXTURE-008 calibration, "
            "not an attested Ugaritic date conversion."
        ),
    }


def role_activity(role: str, seasonal: dict[str, Any]) -> dict[str, Any]:
    base = dict(ROLE_ACTIVITY.get(role, {"domain": "other", "activity": role.replace("_", " ")}))
    if base["domain"] == "agriculture":
        base["activity"] = seasonal["farm_activity"]
        base["seasonal_intensity"] = seasonal["agricultural_intensity"]
    elif role == "seasonal_worker" and seasonal["agricultural_intensity"] >= 0.85:
        base["activity"] = f"seasonal household/harvest labor: {seasonal['farm_activity']}"
        base["seasonal_intensity"] = seasonal["agricultural_intensity"]
    return base


def weekly_cycle_due(day: int) -> bool:
    return int(day) > 0 and int(day) % 7 == 0


def household_ritual_due(day: int) -> bool:
    # Regular observance cadence is a fixture used to make household religion causally
    # present; it is not an attested Ugaritic weekly/monthly schedule.
    return int(day) > 0 and int(day) % 30 == 0


def communal_feast_due(day: int, *, start_day_of_year: int = 120) -> bool:
    # One communal rite/feast checkpoint near the close of the harvest phase. The exact
    # date is deliberately model-owned and labeled ASM-FIXTURE-010.
    doy = calendar_context(day, start_day_of_year=start_day_of_year)["day_of_year"]
    return doy in {150, 270}


def palace_labor_cycle_due(day: int) -> bool:
    # Cadence is an explicit test fixture for institutional extraction pressure.
    return int(day) > 0 and int(day) % 35 == 0
