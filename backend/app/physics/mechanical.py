"""
Mechanical Dynamics and Baseline Vibration Physics Model.
Models boxer 4-stroke rotational unbalance, combustion gas pressure excitation,
and reduction gearbox meshing vibration.

Classification: [Engineering Correlation & Mechanical Dynamics]
Formula:
    Vibration_g = V_base + k_rpm * (RPM / RPM_ref)^1.8 + k_load * load
"""

from typing import Dict
from app.config.constants import VIBRATION_BASELINE_G, TAKEOFF_RPM

# -----------------------------------------------------------------------------
# Mechanical Vibration Calibration Parameters
# -----------------------------------------------------------------------------
# [Synthetic Calibration Parameter]
V_IDLE_MIN_G: float = 0.08               # Minimum structural background vibration at idle (g RMS)
V_REF_RPM: float = 5500.0                # Reference RPM for scaling
K_ROTATIONAL_EXCITATION: float = 0.11    # Unbalance / rotational inertial factor
K_COMBUSTION_LOAD_EXCITATION: float = 0.06 # Peak cylinder pressure / torque ripple factor


def compute_baseline_vibration(
    rpm: float,
    engine_load: float,
) -> Dict[str, float]:
    """
    Calculate baseline mechanical vibration in g (RMS) under healthy operating conditions.

    Classification: [Engineering Correlation: Harmonic & Inertial Mechanics]
    Formula:
        Vibration_g = V_base + k_rpm * (RPM / 5500)^1.8 + k_load * load

    Physics Rationale:
        - The 4-cylinder horizontally opposed boxer layout provides natural primary reciprocating balance.
        - Residual vibration arises from:
          1. 2nd order combustion torque ripple (two power pulses per crankshaft revolution).
          2. Small secondary rocking couple due to cylinder bank offset.
          3. Reduction gearbox spur gear tooth meshing (ratio 2.43:1).
        - Higher RPM increases inertial and gearbox meshing frequencies.
        - Higher load increases cylinder peak pressure and torque pulses.

    Args:
        rpm: Engine rotational speed (RPM).
        engine_load: Engine load fraction (0.0 to 1.0).

    Returns:
        Dict containing:
            - expected_vibration_g: Baseline root-mean-square vibration (g RMS)
            - combustion_vibration_component_g: Contribution from combustion gas torque
            - mechanical_vibration_component_g: Contribution from shaft/gearbox rotation
    """
    clamped_rpm = max(800.0, min(TAKEOFF_RPM * 1.15, float(rpm)))
    load = max(0.08, min(1.0, float(engine_load)))

    rpm_ratio = clamped_rpm / V_REF_RPM
    # Inertial and reduction gearbox mechanical vibration
    v_mechanical = K_ROTATIONAL_EXCITATION * (rpm_ratio ** 1.8)

    # Combustion pressure ripple vibration
    v_combustion = K_COMBUSTION_LOAD_EXCITATION * load * (rpm_ratio ** 0.5)

    total_vibration_g = V_IDLE_MIN_G + v_mechanical + v_combustion

    # Physical bounds check
    total_vibration_g = max(0.05, min(0.60, total_vibration_g))

    return {
        "expected_vibration_g": total_vibration_g,
        "combustion_vibration_component_g": v_combustion,
        "mechanical_vibration_component_g": v_mechanical,
    }
