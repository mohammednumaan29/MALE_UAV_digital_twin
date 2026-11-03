"""
Thermal Physics Model: EGT, CHT, and Oil Temperature.
Models combustion thermodynamics, cylinder head liquid-cooling, and oil thermal heat dissipation.

Classification: [Engineering Correlation & Heat Transfer Energy Balance]
References:
- Rotax 914 F Operators Manual (Section 2: Operating Limits).
- Engine Heat Transfer Principles (Heywood / Taylor).
"""

from typing import Dict
from app.config.constants import (
    EGT_NORMAL_C,
    EGT_MAX_C,
    CHT_NORMAL_C,
    CHT_MAX_C,
    OIL_TEMP_NORMAL_C,
    OIL_TEMP_MAX_C,
)

# -----------------------------------------------------------------------------
# Thermal Coefficients & Calibration
# -----------------------------------------------------------------------------
# [Manufacturer Specification Limits]
EGT_IDLE_NOMINAL_C: float = 600.0        # Nominal EGT at low idle (°C)
CHT_IDLE_NOMINAL_C: float = 85.0         # Nominal CHT at low idle (°C)
OIL_TEMP_IDLE_NOMINAL_C: float = 70.0    # Nominal oil temperature at idle (°C)

# [Engineering Correlation Time Constants (Seconds)]
TAU_EGT_SEC: float = 3.0                 # EGT responds rapidly to combustion changes
TAU_CHT_SEC: float = 45.0                # CHT liquid-cooling thermal inertia
TAU_OIL_TEMP_SEC: float = 90.0           # Oil volume (~3 L) thermal inertia


def compute_steady_state_egt(
    engine_load: float,
    rpm: float,
    ambient_temperature_c: float,
    altitude_ft: float,
    fuel_flow_lph: float,
) -> float:
    """
    Calculate steady-state Exhaust Gas Temperature (EGT) in °C.

    Classification: [Engineering Correlation: Documented Combustion Formulation]
    Formula:
        EGT = f(load, RPM, ambient_temp, altitude, fuel_flow)

    Physics Rationale:
        - As engine load increases, combustion heat release increases, driving EGT up from ~600°C to ~820°C.
        - RPM increases cycle frequency and exhaust blowdown velocities.
        - Higher ambient temperature shifts baseline charge air temperature upwards.
        - Higher altitude increases exhaust expansion ratio slightly.
        - High-power takeoff enrichment causes slight cooling compared to lean peak.
    """
    load = max(0.08, min(1.0, float(engine_load)))
    rpm_norm = max(0.2, min(1.1, float(rpm) / 5500.0))
    t_amb = float(ambient_temperature_c)
    alt_factor = max(0.0, float(altitude_ft)) / 10000.0  # +~5°C per 10k ft due to expansion ratio

    # Baseline combustion rise above ambient
    # Idle (~0.15 load): ~580-620°C. Cruise (~0.65 load): ~690-740°C. Max continuous (~0.90 load): ~790-820°C.
    base_delta = 550.0 + 240.0 * (load ** 0.85) + 35.0 * (rpm_norm - 0.8)

    # Ambient temperature influence (exhaust retains fraction of inlet air enthalpy)
    ambient_influence = 0.35 * (t_amb - 15.0)

    # Altitude expansion factor
    alt_influence = 6.0 * alt_factor

    # Fuel enrichment at near WOT (load > 0.90) cools exhaust slightly (rich quenching)
    if load > 0.90:
        rich_quenching = -25.0 * ((load - 0.90) / 0.10)
    else:
        rich_quenching = 0.0

    egt_c = base_delta + ambient_influence + alt_influence + rich_quenching
    return max(400.0, min(EGT_MAX_C * 1.05, egt_c))


def compute_steady_state_cht(
    ambient_temperature_c: float,
    engine_load: float,
    egt_c: float,
) -> float:
    """
    Calculate steady-state Cylinder Head Temperature (CHT) in °C.

    Classification: [Engineering Correlation: Liquid-Cooled Cylinder Head Heat Balance]
    Formula:
        CHT = f(ambient_temp, load, EGT)

    Physics Rationale:
        - Cylinder heads are liquid-cooled with closed circuit water/coolant.
        - Heat flux into the head from combustion chamber scales with load and gas temperature (EGT).
        - Heat rejection through the radiator scales with (T_coolant - T_ambient).
        - Equilibrium CHT represents the balance between combustion heat flux and radiator rejection.
    """
    load = max(0.08, min(1.0, float(engine_load)))
    t_amb = float(ambient_temperature_c)

    # Radiator heat rejection equilibrium with coolant thermostat regulation:
    # Thermostat ensures minimum operating head temperature ~75°C.
    # At idle: ~75-85°C. At cruise (65%): ~110-125°C. At climb / full load: ~128-138°C.
    # Base temperature rise governed by load and combustion gas temperature
    egt_influence = 0.04 * (egt_c - 650.0)
    load_delta = 65.0 + 48.0 * (load ** 1.0) + egt_influence

    # Radiator heat transfer scales with ambient air temperature
    ambient_correction = 0.55 * (t_amb - 15.0)

    cht_c = load_delta + ambient_correction
    # Thermostat prevents overcooling below 72°C
    return max(72.0, min(CHT_MAX_C * 1.08, cht_c))


def compute_steady_state_oil_temperature(
    ambient_temperature_c: float,
    engine_load: float,
    rpm: float | None = None,
) -> float:
    """
    Calculate steady-state Oil Temperature in °C.

    Classification: [Engineering Correlation: Dry Sump Lubrication Heat Balance]
    Formula:
        Oil_Temp = f(ambient_temp, load)

    Physics Rationale:
        - Engine oil absorbs heat from piston undersides (oil spray cooling), turbocharger center bearing,
          and journal bearings.
        - Oil is circulated through an external oil radiator/cooler.
        - At idle: ~65-75°C. At cruise: ~90-100°C. At high load: ~105-115°C.
    """
    load = max(0.08, min(1.0, float(engine_load)))
    t_amb = float(ambient_temperature_c)

    # Base oil temperature rise above ambient
    oil_delta = 54.0 + 45.0 * (load ** 0.9)
    if rpm is not None:
        rpm_ratio = max(0.5, float(rpm) / 5500.0)
        oil_delta += 8.0 * (rpm_ratio - 0.8)

    ambient_correction = 0.45 * (t_amb - 15.0)
    oil_temp_c = oil_delta + ambient_correction
    return max(40.0, min(OIL_TEMP_MAX_C * 1.05, oil_temp_c))


def compute_thermal_state(
    engine_load: float,
    rpm: float,
    ambient_temperature_c: float,
    altitude_ft: float,
    fuel_flow_lph: float,
) -> Dict[str, float]:
    """
    Calculate all steady-state thermal parameters.

    Returns:
        Dict containing:
            - expected_egt_c: Equilibrium EGT (°C)
            - expected_cht_c: Equilibrium CHT (°C)
            - expected_oil_temperature_c: Equilibrium Oil Temperature (°C)
    """
    egt_c = compute_steady_state_egt(
        engine_load=engine_load,
        rpm=rpm,
        ambient_temperature_c=ambient_temperature_c,
        altitude_ft=altitude_ft,
        fuel_flow_lph=fuel_flow_lph,
    )

    cht_c = compute_steady_state_cht(
        ambient_temperature_c=ambient_temperature_c,
        engine_load=engine_load,
        egt_c=egt_c,
    )

    oil_temp_c = compute_steady_state_oil_temperature(
        ambient_temperature_c=ambient_temperature_c,
        engine_load=engine_load,
        rpm=rpm,
    )

    return {
        "expected_egt_c": egt_c,
        "expected_cht_c": cht_c,
        "expected_oil_temperature_c": oil_temp_c,
    }
