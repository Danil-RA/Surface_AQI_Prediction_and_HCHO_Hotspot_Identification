"""
CPCB AQI sub-index breakpoint logic.

This is the ONLY place AQI is computed in the entire codebase.
No breakpoint arithmetic anywhere else — not in routers, not in the frontend.

Reference: CPCB National Air Quality Index (2014).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# CPCB breakpoint tables
# Each entry: (Ih, Il, BPh, BPl) — upper/lower AQI and concentration bounds.
# Concentrations in standard CPCB units for each pollutant.
# ---------------------------------------------------------------------------

# PM2.5 (µg/m³, 24-hr avg)
_PM25_BP = [
    (50,  0,   30,   0),
    (100, 51,  60,   31),
    (200, 101, 90,   61),
    (300, 201, 120,  91),
    (400, 301, 250,  121),
    (500, 401, 380,  251),
]

# PM10 (µg/m³, 24-hr avg)
_PM10_BP = [
    (50,  0,   50,   0),
    (100, 51,  100,  51),
    (200, 101, 250,  101),
    (300, 201, 350,  251),
    (400, 301, 430,  351),
    (500, 401, 500,  431),
]

# NO2 (µg/m³, 24-hr avg)
_NO2_BP = [
    (50,  0,   40,   0),
    (100, 51,  80,   41),
    (200, 101, 180,  81),
    (300, 201, 280,  181),
    (400, 301, 400,  281),
    (500, 401, 800,  401),
]

# SO2 (µg/m³, 24-hr avg)
_SO2_BP = [
    (50,  0,   40,   0),
    (100, 51,  80,   41),
    (200, 101, 380,  81),
    (300, 201, 800,  381),
    (400, 301, 1600, 801),
    (500, 401, 2100, 1601),
]

# CO (mg/m³, 8-hr avg)
_CO_BP = [
    (50,  0,   1.0,  0.0),
    (100, 51,  2.0,  1.1),
    (200, 101, 10.0, 2.1),
    (300, 201, 17.0, 10.1),
    (400, 301, 34.0, 17.1),
    (500, 401, 50.0, 34.1),
]

# O3 (µg/m³, 8-hr avg)
_O3_BP = [
    (50,  0,   50,   0),
    (100, 51,  100,  51),
    (200, 101, 168,  101),
    (300, 201, 208,  169),
    (400, 301, 748,  209),
    (500, 401, 1000, 749),
]

BREAKPOINTS: dict[str, list[tuple[int, int, float, float]]] = {
    "PM2.5": _PM25_BP,
    "PM10":  _PM10_BP,
    "NO2":   _NO2_BP,
    "SO2":   _SO2_BP,
    "CO":    _CO_BP,
    "O3":    _O3_BP,
}

POLLUTANTS = list(BREAKPOINTS.keys())

# ---------------------------------------------------------------------------
# Category definitions (CPCB, stepped — never interpolated)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AQICategory:
    name: str
    color: str  # hex, per SPEC.md §6
    aqi_low: int
    aqi_high: int


CATEGORIES: list[AQICategory] = [
    AQICategory("Good",        "#55A84F",  0,   50),
    AQICategory("Satisfactory","#A3C853",  51,  100),
    AQICategory("Moderate",    "#FFF833",  101, 200),
    AQICategory("Poor",        "#F29C33",  201, 300),
    AQICategory("Very Poor",   "#E93F33",  301, 400),
    AQICategory("Severe",      "#AF2D24",  401, 500),
]


def get_category(aqi: int) -> AQICategory:
    """Return the CPCB category for a given AQI value."""
    for cat in CATEGORIES:
        if cat.aqi_low <= aqi <= cat.aqi_high:
            return cat
    # Clamp to Severe for out-of-range values > 500
    return CATEGORIES[-1]


# ---------------------------------------------------------------------------
# Core sub-index calculation
# ---------------------------------------------------------------------------

def compute_sub_index(pollutant: str, concentration: float) -> Optional[int]:
    """
    Compute the CPCB sub-index for a single pollutant at a given concentration.

    Returns None if concentration is outside all defined breakpoint ranges
    (should not occur with valid sensor data; caller should treat as no-coverage).

    Formula:
        SI = ((Ih - Il) / (BPh - BPl)) * (Cp - BPl) + Il
    """
    if pollutant not in BREAKPOINTS:
        raise ValueError(f"Unknown pollutant: {pollutant!r}. Must be one of {POLLUTANTS}")

    bps = BREAKPOINTS[pollutant]
    for ih, il, bph, bpl in bps:
        if bpl <= concentration <= bph:
            si = ((ih - il) / (bph - bpl)) * (concentration - bpl) + il
            return round(si)
    return None


@dataclass
class SubIndexResult:
    pollutant: str
    concentration: float
    sub_index: Optional[int]
    category: Optional[AQICategory]


def compute_all_sub_indices(
    concentrations: dict[str, float],
) -> list[SubIndexResult]:
    """
    Compute sub-indices for all provided pollutants.

    concentrations: mapping of pollutant name → concentration value.
    Returns a list of SubIndexResult, one per pollutant present.
    """
    results: list[SubIndexResult] = []
    for pollutant, conc in concentrations.items():
        si = compute_sub_index(pollutant, conc)
        cat = get_category(si) if si is not None else None
        results.append(SubIndexResult(
            pollutant=pollutant,
            concentration=conc,
            sub_index=si,
            category=cat,
        ))
    return results


def compute_aqi(
    concentrations: dict[str, float],
) -> tuple[int, str, dict[str, int]]:
    """
    Compute composite AQI from a dict of pollutant concentrations.

    Returns:
        (aqi, dominant_pollutant, sub_indices_dict)
        where aqi = max of all valid sub-indices (CPCB definition).

    Raises ValueError if concentrations is empty or all sub-indices are None.
    """
    results = compute_all_sub_indices(concentrations)
    valid = [r for r in results if r.sub_index is not None]
    if not valid:
        raise ValueError("No valid sub-indices could be computed from the provided concentrations.")

    dominant = max(valid, key=lambda r: r.sub_index)  # type: ignore[arg-type]
    aqi = dominant.sub_index  # type: ignore[assignment]
    sub_indices = {r.pollutant: r.sub_index for r in valid if r.sub_index is not None}
    return aqi, dominant.pollutant, sub_indices
