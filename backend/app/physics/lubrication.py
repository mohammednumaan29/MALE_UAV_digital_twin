"""
Lubrication and Oil Pressure Physics Model.
Models dry-sump forced lubrication, positive-displacement trochoid pump flow,
temperature-dependent kinematic viscosity, and pressure relief valve regulation.

Classification: [Standard Physical Equation & Engineering Correlation]
Formulas:
    mu(T) = mu_ref * exp(B / (T_c + 95))
    P_raw = k_pump * RPM * (mu / mu_ref)
    P_oil = min(P_relief_valve, max(P_min, P_raw))
"""

import math
from typing import Dict
from app.config.constants import (
    OIL_PRESS_NORMAL_BAR,
    OIL_PRESS_MIN_BAR,
    OIL_PRESS_MAX_BAR,
)

# -----------------------------------------------------------------------------
# Lubrication Engineering Parameters
# -----------------------------------------------------------------------------
# [Manufacturer Specification Limits]
RELIEF_VALVE_SETTING_BAR: float = 4.85     # Spring-loaded PRV opening pressure (bar)
ABSOLUTE_MIN_PRESSURE_BAR: float = 1.20    # Lower physical boundary under catastrophic conditions (bar)

# [Engineering Assumption: SAE 10W-40 Multigrade Viscosity Curve]
# Kinematic viscosity ~ 95 cSt @ 40°C, 14.5 cSt @ 100°C, 7.5 cSt @ 130°C
T_REF_C: float = 95.0                      # Reference operating temperature (°C)
VISCOSITY_B_COEFF: float = 420.0           # Vogel temperature sensitivity coefficient


def compute_relative_viscosity(oil_temperature_c: float) -> float:
    """
    Calculate normalized oil viscosity relative to standard 95°C operating baseline.

    Classification: [Standard Physical Equation: Vogel / Reynolds Viscosity Model]
    Formula:
        mu_rel = exp( B * (1/(T + 95) - 1/(T_ref + 95)) )
    """
    t_c = max(10.0, float(oil_temperature_c))
    # Relative viscosity: 1.0 at 95°C, ~3.0 at 40°C (cold start), ~0.65 at 125°C (hot thin oil)
    exponent = VISCOSITY_B_COEFF * ((1.0 / (t_c + 95.0)) - (1.0 / (T_REF_C + 95.0)))
    mu_rel = math.exp(exponent)
    return max(0.40, min(5.0, mu_rel))


def compute_oil_pressure(
    rpm: float,
    oil_temperature_c: float
) -> Dict[str, float]:
    """
    Compute engine oil pressure in bar.

    Classification: [Engineering Correlation: Trochoid Pump Hydrodynamic Flow]
    Formula:
        P_oil = f(RPM, oil_temp)

    Physics Rationale:
        - Trochoid oil pump delivers volumetric flow proportional to engine speed (RPM).
        - Resistance to flow across main, rod, and camshaft bearing hydrodynamic clearances
          creates backpressure proportional to dynamic viscosity.
        - Spring-loaded pressure relief valve opens to bypass excess flow above ~4.85 bar.
        - At nominal warm cruise (5000 RPM, 95°C), oil pressure is ~3.5 to 4.2 bar.
        - At warm idle (1400 RPM, 95°C), oil pressure stabilizes around ~1.8 to 2.2 bar.
        - At cold startup (40°C), higher viscosity drives pressure directly to the relief limit.

    Args:
        rpm: Engine rotational speed (RPM).
        oil_temperature_c: Lubricating oil temperature (°C).

    Returns:
        Dict containing:
            - expected_oil_pressure_bar: Equilibrium oil pressure (bar)
            - relative_viscosity: Oil viscosity relative to 95°C baseline
            - relief_valve_active: Boolean indicating if PRV is actively bypassing flow
    """
    clamped_rpm = max(600.0, float(rpm))
    t_oil = float(oil_temperature_c)

    mu_rel = compute_relative_viscosity(t_oil)

    # Base hydrodynamic flow pressure before relief valve
    # Scaled such that 5000 RPM at mu_rel=1.0 generates ~3.8 bar
    rpm_norm = clamped_rpm / 5000.0
    # Positive displacement pump: linear with RPM, hydrodynamic clearance resistance with viscosity
    p_unregulated = 1.0 + 2.8 * (rpm_norm ** 0.85) * (mu_rel ** 0.55)

    # Pressure relief valve clipping
    if p_unregulated >= RELIEF_VALVE_SETTING_BAR:
        oil_pressure_bar = RELIEF_VALVE_SETTING_BAR
        prv_active = True
    else:
        oil_pressure_bar = p_unregulated
        prv_active = False

    # Ensure pressure never drops below physical minimum
    oil_pressure_bar = max(ABSOLUTE_MIN_PRESSURE_BAR, oil_pressure_bar)

    return {
        "expected_oil_pressure_bar": oil_pressure_bar,
        "relative_viscosity": mu_rel,
        "relief_valve_active": prv_active,
    }
