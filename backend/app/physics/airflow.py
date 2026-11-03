"""
Engine Airflow Physics Model for Four-Stroke Aero-Piston Engine.
Calculates volumetric efficiency and instantaneous air mass flow rate.

Classification: [Standard Physical Equation & Engineering Correlation]
Formula:
    m_dot_air = rho_manifold * V_d * (RPM / 120) * eta_v
"""

from typing import Dict
from app.config.constants import ENGINE_DISPLACEMENT_L

# -----------------------------------------------------------------------------
# Airflow Parameters
# -----------------------------------------------------------------------------
# [Manufacturer Specification]
DISPLACEMENT_M3: float = ENGINE_DISPLACEMENT_L * 1e-3   # 0.0012112 m³ (1211.2 cc)
GAS_CONSTANT_AIR: float = 287.05287                     # J/(kg·K)

# [Engineering Assumption: Volumetric Efficiency Model]
ETA_V_PEAK: float = 0.88                                # Peak volumetric efficiency
RPM_PEAK_TORQUE: float = 5000.0                         # RPM where cylinder filling peaks


def compute_volumetric_efficiency(rpm: float, manifold_pressure_bar: float) -> float:
    """
    Compute volumetric efficiency (eta_v) as a function of engine speed and manifold pressure.

    Classification: [Engineering Correlation]
    """
    clamped_rpm = max(800.0, min(6500.0, float(rpm)))
    # Parabolic curve centered on peak torque speed (5000 RPM)
    rpm_delta = (clamped_rpm - RPM_PEAK_TORQUE) / 3000.0
    eta_rpm = ETA_V_PEAK - 0.08 * (rpm_delta ** 2)

    # Slight improvement under positive turbo manifold boost
    p_boost_factor = 1.0 + 0.03 * max(0.0, manifold_pressure_bar - 1.0)
    eta_v = max(0.65, min(0.95, eta_rpm * p_boost_factor))
    return eta_v


def compute_airflow_state(
    rpm: float,
    manifold_pressure_bar: float,
    manifold_temperature_k: float,
) -> Dict[str, float]:
    """
    Calculate cylinder air mass flow rate for the 4-stroke cycle.

    Classification: [Standard Physical Equation]
    Formula:
        m_dot_air = rho_manifold * V_d * (RPM / 120) * eta_v

    Args:
        rpm: Engine rotational speed.
        manifold_pressure_bar: Absolute intake manifold pressure (bar).
        manifold_temperature_k: Air temperature in the manifold (K).

    Returns:
        Dict containing:
            - air_density_manifold_kgm3: Density of charge air entering cylinders
            - volumetric_efficiency: Volumetric efficiency ratio (eta_v)
            - air_mass_flow_kg_s: Air mass flow rate in kg/s
            - air_mass_flow_kg_h: Air mass flow rate in kg/h
    """
    rpm_safe = max(500.0, float(rpm))
    p_pa = max(10000.0, float(manifold_pressure_bar) * 100000.0)
    t_k = max(180.0, float(manifold_temperature_k))

    # Charge air density inside intake manifold
    # [Standard Physical Equation: Ideal Gas Law]
    rho_manifold = p_pa / (GAS_CONSTANT_AIR * t_k)

    # Volumetric efficiency
    eta_v = compute_volumetric_efficiency(rpm_safe, manifold_pressure_bar)

    # Air mass flow rate: 4-stroke intake strokes per second = RPM / 120
    # [Standard Physical Equation]
    air_mass_flow_kg_s = rho_manifold * DISPLACEMENT_M3 * (rpm_safe / 120.0) * eta_v
    air_mass_flow_kg_h = air_mass_flow_kg_s * 3600.0

    return {
        "air_density_manifold_kgm3": rho_manifold,
        "volumetric_efficiency": eta_v,
        "air_mass_flow_kg_s": air_mass_flow_kg_s,
        "air_mass_flow_kg_h": air_mass_flow_kg_h,
    }
