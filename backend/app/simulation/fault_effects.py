"""
Fault Effects Physics and Degradation Models.
Modifies baseline healthy engine states according to physical fault categories and continuous severity.

Classification: [Physical Degradation Model]
Rules:
- Gradual severity (0.0 to 1.0 / 0% to 100%)
- Modifies physical parameters realistically rather than random spikes.
"""

from typing import Dict, Any
from app.config.constants import FaultCategory, canonical_fault_name


def apply_fault_effects(
    base_state: Dict[str, Any],
    fault_type: FaultCategory | str,
    severity: float,
) -> Dict[str, Any]:
    """
    Apply physical fault degradation offsets to the base engine state.

    Args:
        base_state: Baseline healthy telemetry state dictionary.
        fault_type: FaultCategory enum or string ('NORMAL', 'FUEL_MIXTURE', 'OVERHEATING', 'LUBRICATION', 'VIBRATION', 'SENSOR_ANOMALY').
        severity: Fault severity fraction (0.0 = healthy, 1.0 = 100% severe failure).

    Returns:
        Dict containing telemetry with physical degradation applied.
    """
    s = max(0.0, min(1.0, float(severity)))
    f_type = FaultCategory(fault_type) if isinstance(fault_type, str) else fault_type
    f_name = canonical_fault_name(f_type)

    if s <= 0.001 or f_type == FaultCategory.NORMAL:
        result = dict(base_state)
        result["active_fault"] = FaultCategory.NORMAL.value
        result["fault_severity"] = 0.0
        return result

    degraded = dict(base_state)

    if f_name == canonical_fault_name(FaultCategory.FUEL_MIXTURE_DEGRADATION):
        # Carburetor / Fuel-Mixture Delivery Degradation:
        # Jet clogging or float needle restriction leads to progressive lean-out.
        # - Fuel flow drops by up to 32%
        # - EGT rises strongly initially (peak lean), then levels off at extreme lean
        # - CHT rises moderately (+12 to +22 °C) due to lean flame temperatures
        # - Power drops by up to 28%
        # - RPM droops by up to 450 RPM
        # - Combustion roughness increases vibration (+0.05 to +0.22 g)
        ff_factor = 1.0 - (0.32 * s)
        egt_delta = 70.0 * s if s <= 0.7 else (70.0 * 0.7) - 30.0 * (s - 0.7)
        cht_delta = 18.0 * (s ** 0.8)
        pwr_factor = 1.0 - (0.28 * s)
        rpm_delta = -420.0 * (s ** 0.9)
        vib_delta = 0.20 * (s ** 1.2)

        degraded["fuel_flow_lph"] = max(2.0, degraded["fuel_flow_lph"] * ff_factor)
        degraded["egt_c"] = degraded["egt_c"] + egt_delta
        degraded["cht_c"] = degraded["cht_c"] + cht_delta
        degraded["power_kw"] = max(1.0, degraded["power_kw"] * pwr_factor)
        degraded["rpm"] = max(900.0, degraded["rpm"] + rpm_delta)
        degraded["vibration_g"] = degraded["vibration_g"] + vib_delta

    elif f_name == canonical_fault_name(FaultCategory.OVERHEATING):
        # Thermal / Cooling System Degradation:
        # Radiator blockage, coolant pump cavitation, or stuck thermostat.
        # - CHT rises severely (+15 to +48 °C, pushing past 135 °C limit)
        # - EGT rises moderately (+10 to +32 °C)
        # - Oil temperature rises significantly (+12 to +35 °C)
        # - Oil pressure decreases (-0.4 to -0.85 bar) due to severe thermal viscosity decay
        # - Power decreases slightly (-3% to -10%) due to charge heating
        # - Vibration increases slightly (+0.03 to +0.07 g) from thermal expansion friction
        cht_delta = 45.0 * (s ** 0.85)
        egt_delta = 28.0 * (s ** 0.9)
        oil_temp_delta = 32.0 * (s ** 0.9)
        oil_press_delta = -0.80 * (s ** 0.8)
        pwr_factor = 1.0 - (0.10 * s)
        vib_delta = 0.06 * s

        degraded["cht_c"] = degraded["cht_c"] + cht_delta
        degraded["egt_c"] = degraded["egt_c"] + egt_delta
        degraded["oil_temperature_c"] = degraded["oil_temperature_c"] + oil_temp_delta
        degraded["oil_pressure_bar"] = max(0.8, degraded["oil_pressure_bar"] + oil_press_delta)
        degraded["power_kw"] = max(1.0, degraded["power_kw"] * pwr_factor)
        degraded["vibration_g"] = degraded["vibration_g"] + vib_delta

    elif f_name == canonical_fault_name(FaultCategory.LUBRICATION_DEGRADATION):
        # Lubrication Degradation:
        # Oil pump wear, oil line leak, or severe journal bearing clearance loss.
        # - Oil pressure drops drastically (-1.0 to -2.4 bar, often below 1.5 bar minimum)
        # - Oil temperature rises (+14 to +30 °C) from bearing friction
        # - Vibration increases (+0.08 to +0.26 g) from bearing unbalance & metal contact
        # - RPM droops (-100 to -400 RPM)
        # - Power drops (-6% to -18%) due to parasitic friction
        oil_press_delta = -2.20 * (s ** 0.75)
        oil_temp_delta = 26.0 * (s ** 0.9)
        vib_delta = 0.22 * (s ** 1.1)
        rpm_delta = -380.0 * (s ** 0.85)
        pwr_factor = 1.0 - (0.16 * s)

        degraded["oil_pressure_bar"] = max(0.6, degraded["oil_pressure_bar"] + oil_press_delta)
        degraded["oil_temperature_c"] = degraded["oil_temperature_c"] + oil_temp_delta
        degraded["vibration_g"] = degraded["vibration_g"] + vib_delta
        degraded["rpm"] = max(800.0, degraded["rpm"] + rpm_delta)
        degraded["power_kw"] = max(1.0, degraded["power_kw"] * pwr_factor)

    elif f_name == canonical_fault_name(FaultCategory.ABNORMAL_VIBRATION):
        # Abnormal Mechanical Vibration:
        # Reduction gearbox meshing fault, engine mounting damper tear, or propeller unbalance.
        # - Vibration spikes dramatically (+0.18 to +0.58 g RMS)
        # - RPM instability / flutter
        # - Small power reduction at high severity (-2% to -8%)
        vib_delta = 0.55 * (s ** 0.8)
        pwr_factor = 1.0 - (0.08 * s)
        rpm_instability = 45.0 * s

        degraded["vibration_g"] = degraded["vibration_g"] + vib_delta
        degraded["power_kw"] = max(1.0, degraded["power_kw"] * pwr_factor)
        # Instability offset
        degraded["rpm"] = max(800.0, degraded["rpm"] - rpm_instability)

    elif f_name == canonical_fault_name(FaultCategory.SENSOR_ANOMALY):
        # Sensor Transducer Anomaly (Bias / Drift):
        # Induces calibrated bias on CHT and EGT for testing anomaly detection without engine damage
        degraded["cht_c"] = degraded["cht_c"] + 38.0 * s
        degraded["oil_temperature_c"] = degraded["oil_temperature_c"] - 25.0 * s

    # Ensure engine load and torque match degraded power and RPM
    # [Physical Consistency Update]
    omega = (2.0 * 3.1415926535 * degraded["rpm"]) / 60.0
    degraded["power_kw"] = round(degraded["power_kw"], 1)
    degraded["torque_nm"] = round((degraded["power_kw"] * 1000.0) / max(10.0, omega), 1)

    degraded["active_fault"] = f_type.value
    degraded["fault_severity"] = round(s, 3)

    return degraded
