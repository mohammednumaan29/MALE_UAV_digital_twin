"""
Engine Power, Torque, and Mechanical Work Physics Model.
Implements torque from angular velocity and power balance for the Rotax 914.

Classification: [Standard Physical Equation & Manufacturer Specification]
Formulas:
    omega = 2 * pi * RPM / 60
    P = T * omega  ==>  T = P / omega
"""

import math
from typing import Dict
from app.config.constants import (
    MAX_CONTINUOUS_POWER_KW,
    TAKEOFF_POWER_KW,
    MAX_CONTINUOUS_RPM,
    TAKEOFF_RPM,
    IDLE_RPM,
)

# -----------------------------------------------------------------------------
# Power & Torque Baseline Constants
# -----------------------------------------------------------------------------
# [Manufacturer Specification]
IDLE_POWER_KW: float = 3.5              # Engine power output at idle (kW)
PEAK_TORQUE_NM: float = 144.0           # Peak torque rating (N·m @ ~4900 RPM)


def compute_angular_velocity(rpm: float) -> float:
    """
    Compute shaft angular velocity in rad/s.
    Classification: [Standard Physical Equation]
    Formula: omega = (2 * pi * RPM) / 60
    """
    return (2.0 * math.pi * max(100.0, float(rpm))) / 60.0


def compute_expected_rpm(throttle_pct: float) -> float:
    """
    Determine equilibrium expected RPM from throttle setting under standard propeller governor load curve.
    Classification: [Engineering Correlation: Propeller Governor / Pitch Matching]
    Calibration:
        - 0% throttle -> 1400 RPM (ground idle)
        - 10% throttle -> ~1860 RPM (high idle / taxi)
        - 65% throttle -> 5100 RPM (cruise)
        - 90% throttle -> 5500 RPM (max continuous)
        - 100% throttle -> 5800 RPM (takeoff)
    """
    t = max(0.0, min(100.0, float(throttle_pct)))
    if t <= 0.0:
        return IDLE_RPM
    elif t >= 100.0:
        return TAKEOFF_RPM
    elif t <= 65.0:
        # Ground idle to cruise band
        frac = (t / 65.0) ** 1.15
        return IDLE_RPM + frac * (5100.0 - IDLE_RPM)
    else:
        # Cruise to takeoff band
        frac = ((t - 65.0) / 35.0) ** 0.88
        return 5100.0 + frac * (TAKEOFF_RPM - 5100.0)


def compute_power_and_torque(
    rpm: float,
    throttle_pct: float,
    manifold_pressure_bar: float,
    air_density_kgm3: float,
) -> Dict[str, float]:
    """
    Calculate engine indicated/brake power, torque, and instantaneous load.

    Classification: [Standard Physical Equation & Manufacturer Specification]
    Formulas:
        P = f(RPM, throttle, MAP, rho_air)
        T = P_watts / omega

    Args:
        rpm: Engine rotational speed (RPM).
        throttle_pct: Throttle setting (0 to 100%).
        manifold_pressure_bar: Manifold absolute pressure (bar).
        air_density_kgm3: Air density (kg/m³).

    Returns:
        Dict containing:
            - power_kw: Brake power in kW
            - power_hp: Brake power in horsepower (hp)
            - torque_nm: Engine torque (N·m)
            - engine_load: Normalized engine load fraction (0.0 to 1.0)
            - angular_velocity_rad_s: Shaft speed (rad/s)
    """
    clamped_rpm = max(IDLE_RPM * 0.7, min(TAKEOFF_RPM * 1.15, float(rpm)))
    t_factor = max(0.0, min(100.0, float(throttle_pct))) / 100.0
    omega = compute_angular_velocity(clamped_rpm)

    # Normalized engine load factor: derived from throttle and manifold pressure
    # [Engineering Correlation]
    map_norm = max(0.35, min(1.33, float(manifold_pressure_bar)))
    load = 0.12 + 0.88 * (0.60 * t_factor + 0.40 * ((map_norm - 0.40) / 0.93))
    engine_load = max(0.08, min(1.0, load))

    # Power generation calibrated to Rotax 914 performance curve
    # [Manufacturer Specification Calibration]
    # Max continuous: 73.5 kW @ 5500 RPM, Takeoff: 84.5 kW @ 5800 RPM
    if t_factor >= 0.95 and clamped_rpm >= 5650.0:
        target_pot = TAKEOFF_POWER_KW
        rpm_ref = TAKEOFF_RPM
    else:
        target_pot = MAX_CONTINUOUS_POWER_KW
        rpm_ref = MAX_CONTINUOUS_RPM

    rpm_frac = min(1.0, clamped_rpm / rpm_ref)
    power_kw = IDLE_POWER_KW + (target_pot - IDLE_POWER_KW) * (engine_load ** 0.85) * (rpm_frac ** 1.0)

    # Sanity clamping based on Rotax 914 performance envelope
    power_kw = max(2.5, min(TAKEOFF_POWER_KW, power_kw))
    power_hp = power_kw * 1.34102

    # Torque from mechanical relationship: P = T * omega  ==> T = (P_kW * 1000) / omega
    # [Standard Physical Equation]
    torque_nm = (power_kw * 1000.0) / omega

    return {
        "power_kw": power_kw,
        "power_hp": power_hp,
        "torque_nm": torque_nm,
        "engine_load": engine_load,
        "angular_velocity_rad_s": omega,
    }
