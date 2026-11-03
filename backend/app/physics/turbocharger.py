"""
Turbocharger and Manifold Pressure Physics Model for Rotax 914.
Models wastegate control (TCU), boost schedule, critical altitude, and intercooler thermodynamics.

Classification: [Manufacturer Specification & Engineering Correlation]
References:
- Rotax 914 F Operators Manual (Section 2: Technical Data).
- Gas Turbine / Turbocharger Thermodynamic Fundamentals.
"""

import math
from typing import Dict

# -----------------------------------------------------------------------------
# Rotax 914 Turbocharger Engineering Parameters
# -----------------------------------------------------------------------------
# [Manufacturer Specification]
MAP_IDLE_BAR: float = 0.40              # Manifold pressure at idle vacuum (~12 inHg / 0.40 bar)
MAP_CONTINUOUS_MAX_BAR: float = 1.18    # Max continuous manifold pressure (35.4 inHg / 1.18 bar)
MAP_TAKEOFF_MAX_BAR: float = 1.33       # Max takeoff manifold pressure (39.9 inHg / 1.33 bar, 5-min limit)

# [Engineering Assumption]
CRITICAL_ALTITUDE_FT: float = 16000.0   # Turbocharger critical altitude (~4,877 m / 16,000 ft)
MAX_COMPRESSOR_PR: float = 2.15         # Maximum compressor pressure ratio (P_out / P_in)
COMPRESSOR_EFFICIENCY: float = 0.72     # Isentropic efficiency of compressor (eta_c)
INTERCOOLER_EFFICIENCY: float = 0.65    # Intercooler thermal effectiveness (eta_ic)
GAMMA_AIR: float = 1.40                 # Specific heat ratio for air


def compute_manifold_state(
    throttle_pct: float,
    ambient_pressure_bar: float,
    ambient_temperature_k: float,
    altitude_ft: float,
    rpm: float | None = None
) -> Dict[str, float]:
    """
    Calculate manifold absolute pressure (MAP), boost ratio, and manifold charge temperature.

    Args:
        throttle_pct: Throttle setting (0.0% to 100.0%).
        ambient_pressure_bar: Ambient atmospheric static pressure in bar.
        ambient_temperature_k: Ambient air temperature in Kelvin.
        altitude_ft: Flight altitude in feet.
        rpm: Optional engine RPM for dynamic flow correction.

    Returns:
        Dict containing:
            - manifold_pressure_bar: Absolute manifold pressure (bar)
            - manifold_pressure_inhg: Manifold pressure in inches of mercury (inHg)
            - manifold_temperature_k: Air temperature inside intake manifold (K)
            - boost_pressure_bar: Boost above ambient pressure (bar)
            - pressure_ratio: Compressor/throttle pressure ratio (P_map / P_amb)
            - wastegate_position_pct: 0% = fully open (no boost), 100% = fully closed
            - is_boosted: True if MAP > ambient_pressure_bar
    """
    t_clamped = max(0.0, min(100.0, float(throttle_pct)))
    p_amb = max(0.1, float(ambient_pressure_bar))
    t_amb = max(180.0, float(ambient_temperature_k))
    alt_ft = max(0.0, float(altitude_ft))

    # Phase A: Off-boost Naturally Aspirated Regime (Throttle 0% to 50%)
    # [Engineering Correlation: Butterfly Throttle Restriction]
    if t_clamped <= 50.0:
        throttle_factor = t_clamped / 50.0
        # Smooth interpolation from idle manifold vacuum (~0.40 bar) to ambient pressure
        p_target = MAP_IDLE_BAR + throttle_factor * (p_amb - MAP_IDLE_BAR)
        wastegate_pos = 0.0
    else:
        # Phase B: Turbocharger TCU Boost Schedule (Throttle 50% to 100%)
        # Rotax 914 TCU regulates ABSOLUTE manifold pressure up to critical altitude (~16,000 ft).
        # Throttle 50%: ~1.00 bar (sea level ambient)
        # Throttle 65%: ~1.10 bar (cruise boost)
        # Throttle 90%: 1.18 bar (max continuous boost limit)
        # Throttle 100%: 1.33 bar (takeoff boost limit)
        if t_clamped <= 90.0:
            frac = (t_clamped - 50.0) / 40.0
            target_map = 1.00 + frac * (MAP_CONTINUOUS_MAX_BAR - 1.00)
        else:
            frac = (t_clamped - 90.0) / 10.0
            target_map = MAP_CONTINUOUS_MAX_BAR + frac * (MAP_TAKEOFF_MAX_BAR - MAP_CONTINUOUS_MAX_BAR)

        # Critical Altitude Compensation:
        # Compressor cannot exceed maximum pressure ratio Pi_max (2.15)
        # [Physical Constraint: Compressor Pressure Ratio Limit]
        max_deliverable_map = p_amb * MAX_COMPRESSOR_PR
        p_target = min(target_map, max_deliverable_map)

        # Wastegate Position (duty cycle required to maintain boost)
        if p_target > p_amb:
            req_pr = p_target / p_amb
            wastegate_pos = min(100.0, ((req_pr - 1.0) / (MAX_COMPRESSOR_PR - 1.0)) * 100.0)
        else:
            wastegate_pos = 0.0

    p_map = max(MAP_IDLE_BAR, p_target)
    pressure_ratio = p_map / p_amb

    # Temperature rise across compressor & intercooler cooling
    # [Standard Physical Equation: Isentropic Compression]
    if pressure_ratio > 1.0:
        isentropic_factor = math.pow(pressure_ratio, (GAMMA_AIR - 1.0) / GAMMA_AIR) - 1.0
        t_comp_out = t_amb * (1.0 + isentropic_factor / COMPRESSOR_EFFICIENCY)
        # Intercooler effectiveness: T_map = T_comp_out - eta_ic * (T_comp_out - T_amb)
        t_map = t_comp_out - INTERCOOLER_EFFICIENCY * (t_comp_out - t_amb)
    else:
        # Throttle expansion causes slight adiabatic cooling or remains near ambient
        t_map = t_amb

    manifold_inhg = p_map * 29.53  # 1 bar = 29.53 inHg
    boost_bar = max(0.0, p_map - p_amb)

    return {
        "manifold_pressure_bar": p_map,
        "manifold_pressure_inhg": manifold_inhg,
        "manifold_temperature_k": t_map,
        "manifold_temperature_c": t_map - 273.15,
        "boost_pressure_bar": boost_bar,
        "pressure_ratio": pressure_ratio,
        "wastegate_position_pct": wastegate_pos,
        "is_boosted": p_map > p_amb,
    }
