"""
Automated Physics Model Tests.
Validates atmosphere, turbocharger, airflow, power, combustion, thermal,
lubrication, mechanical vibration, and full integrated engine physics.

Phase 1 Verification.
"""

import math
import pytest
from app.physics.atmosphere import compute_atmospheric_state
from app.physics.turbocharger import compute_manifold_state
from app.physics.airflow import compute_airflow_state, compute_volumetric_efficiency
from app.physics.power import compute_angular_velocity, compute_expected_rpm, compute_power_and_torque
from app.physics.combustion import compute_fuel_flow, compute_air_fuel_ratio
from app.physics.thermal import (
    compute_steady_state_egt,
    compute_steady_state_cht,
    compute_steady_state_oil_temperature,
    compute_thermal_state,
)
from app.physics.lubrication import compute_oil_pressure, compute_relative_viscosity
from app.physics.mechanical import compute_baseline_vibration
from app.physics.engine_model import Rotax914PhysicsModel


def test_atmosphere_isa_equations():
    """Verify atmospheric pressure, temperature, and density decay with altitude."""
    sea_level = compute_atmospheric_state(altitude_ft=0, ambient_temperature_c=15.0)
    alt_10k = compute_atmospheric_state(altitude_ft=10000, ambient_temperature_c=-4.8)
    alt_25k = compute_atmospheric_state(altitude_ft=25000, ambient_temperature_c=-34.5)

    # Sea level sanity
    assert abs(sea_level["pressure_pa"] - 101325.0) < 50.0
    assert abs(sea_level["density_kgm3"] - 1.225) < 0.02
    assert sea_level["pressure_bar"] > 1.0

    # Monotonic decay
    assert sea_level["pressure_pa"] > alt_10k["pressure_pa"] > alt_25k["pressure_pa"]
    assert sea_level["density_kgm3"] > alt_10k["density_kgm3"] > alt_25k["density_kgm3"]
    assert sea_level["pressure_bar"] > alt_10k["pressure_bar"] > alt_25k["pressure_bar"]

    # Non-negative
    for state in [sea_level, alt_10k, alt_25k]:
        assert state["pressure_pa"] > 0
        assert state["density_kgm3"] > 0
        assert state["temperature_k"] > 0


def test_turbocharger_boost_and_critical_altitude():
    """Verify turbocharger manifold pressure across throttle range and altitude limits."""
    # At sea level (P_amb ~ 1.013 bar)
    p_amb = 1.013
    t_amb = 288.15

    # Low throttle: vacuum
    idle_state = compute_manifold_state(throttle_pct=10.0, ambient_pressure_bar=p_amb, ambient_temperature_k=t_amb, altitude_ft=0)
    assert idle_state["manifold_pressure_bar"] < p_amb
    assert idle_state["wastegate_position_pct"] == 0.0

    # Cruise throttle: boost active
    cruise_state = compute_manifold_state(throttle_pct=75.0, ambient_pressure_bar=p_amb, ambient_temperature_k=t_amb, altitude_ft=5000)
    assert cruise_state["manifold_pressure_bar"] >= p_amb
    assert cruise_state["is_boosted"] is True

    # Takeoff throttle: max boost
    takeoff_state = compute_manifold_state(throttle_pct=100.0, ambient_pressure_bar=p_amb, ambient_temperature_k=t_amb, altitude_ft=0)
    assert takeoff_state["manifold_pressure_bar"] <= 1.33 + 0.01
    assert takeoff_state["manifold_pressure_bar"] > cruise_state["manifold_pressure_bar"]

    # Critical altitude test (e.g. 25,000 ft where P_amb ~ 0.37 bar)
    high_alt_p = 0.375
    high_alt_state = compute_manifold_state(throttle_pct=100.0, ambient_pressure_bar=high_alt_p, ambient_temperature_k=230.0, altitude_ft=25000)
    # Beyond critical altitude, max MAP is limited by compressor PR (2.15 * 0.375 ~ 0.8 bar)
    assert high_alt_state["manifold_pressure_bar"] < 1.33
    assert high_alt_state["manifold_pressure_bar"] <= high_alt_p * 2.16


def test_airflow_dynamics():
    """Verify volumetric efficiency and mass airflow calculations."""
    eta_v = compute_volumetric_efficiency(rpm=5000, manifold_pressure_bar=1.18)
    assert 0.70 <= eta_v <= 0.95

    flow = compute_airflow_state(rpm=5000, manifold_pressure_bar=1.15, manifold_temperature_k=305.0)
    assert flow["air_mass_flow_kg_s"] > 0.02
    assert flow["air_mass_flow_kg_h"] > 80.0
    assert flow["air_density_manifold_kgm3"] > 1.10


def test_power_torque_relationship():
    """Verify power, torque, and P = T * omega physics."""
    rpm = 5500.0
    throttle = 85.0
    power_state = compute_power_and_torque(
        rpm=rpm,
        throttle_pct=throttle,
        manifold_pressure_bar=1.18,
        air_density_kgm3=1.20
    )

    p_kw = power_state["power_kw"]
    t_nm = power_state["torque_nm"]
    omega = power_state["angular_velocity_rad_s"]

    # Verify P = T * omega
    p_calc_kw = (t_nm * omega) / 1000.0
    assert abs(p_kw - p_calc_kw) < 0.1

    # Takeoff power test
    takeoff = compute_power_and_torque(rpm=5800, throttle_pct=100.0, manifold_pressure_bar=1.33, air_density_kgm3=1.22)
    assert 80.0 <= takeoff["power_kw"] <= 87.0


def test_combustion_energy_balance():
    """Verify fuel flow energy balance and LPH calculations."""
    comb = compute_fuel_flow(power_kw=65.0, engine_load=0.80)
    # At 65 kW, fuel flow should realistically be between 16 and 26 L/h
    assert 15.0 <= comb["fuel_flow_lph"] <= 26.0
    assert comb["thermal_efficiency"] > 0.22
    assert comb["fuel_flow_kg_s"] > 0


def test_thermal_correlations():
    """Verify EGT, CHT, and oil temperature physics."""
    # Low load vs High load
    egt_low = compute_steady_state_egt(engine_load=0.2, rpm=2000, ambient_temperature_c=15, altitude_ft=0, fuel_flow_lph=5.0)
    egt_high = compute_steady_state_egt(engine_load=0.8, rpm=5200, ambient_temperature_c=15, altitude_ft=0, fuel_flow_lph=19.0)
    assert egt_high > egt_low
    assert 550.0 <= egt_low <= 680.0
    assert 680.0 <= egt_high <= 860.0

    # CHT increases with load
    cht_low = compute_steady_state_cht(ambient_temperature_c=15, engine_load=0.2, egt_c=egt_low)
    cht_high = compute_steady_state_cht(ambient_temperature_c=15, engine_load=0.8, egt_c=egt_high)
    assert cht_high > cht_low
    assert 70.0 <= cht_low <= 100.0
    assert 105.0 <= cht_high <= 140.0

    # Oil temp increases with load and ambient temp
    oil_low = compute_steady_state_oil_temperature(ambient_temperature_c=15, engine_load=0.2, rpm=2000)
    oil_high = compute_steady_state_oil_temperature(ambient_temperature_c=15, engine_load=0.8, rpm=5200)
    oil_hot_day = compute_steady_state_oil_temperature(ambient_temperature_c=38, engine_load=0.8, rpm=5200)
    assert oil_high > oil_low
    assert oil_hot_day > oil_high
    assert 60.0 <= oil_low <= 85.0
    assert 85.0 <= oil_high <= 120.0


def test_lubrication_viscosity_and_pressure():
    """Verify oil pressure response to RPM and temperature."""
    # Cold oil -> higher viscosity -> high pressure (relief valve active)
    cold_lube = compute_oil_pressure(rpm=3000, oil_temperature_c=40.0)
    # Warm oil -> lower viscosity -> normal pressure
    warm_lube = compute_oil_pressure(rpm=3000, oil_temperature_c=95.0)
    # Hot thin oil -> lower pressure
    hot_lube = compute_oil_pressure(rpm=3000, oil_temperature_c=120.0)

    assert cold_lube["relative_viscosity"] > warm_lube["relative_viscosity"] > hot_lube["relative_viscosity"]
    assert cold_lube["expected_oil_pressure_bar"] >= warm_lube["expected_oil_pressure_bar"] >= hot_lube["expected_oil_pressure_bar"]

    # RPM response: at same warm temp (95°C), higher RPM generates higher pressure
    idle_lube = compute_oil_pressure(rpm=1400, oil_temperature_c=95.0)
    cruise_lube = compute_oil_pressure(rpm=5200, oil_temperature_c=95.0)
    assert cruise_lube["expected_oil_pressure_bar"] > idle_lube["expected_oil_pressure_bar"]
    assert idle_lube["expected_oil_pressure_bar"] >= 1.5  # Rotax minimum limit


def test_mechanical_vibration():
    """Verify vibration envelope and scaling with RPM and load."""
    vib_idle = compute_baseline_vibration(rpm=1400, engine_load=0.15)
    vib_cruise = compute_baseline_vibration(rpm=5100, engine_load=0.65)
    vib_takeoff = compute_baseline_vibration(rpm=5800, engine_load=1.0)

    assert vib_takeoff["expected_vibration_g"] > vib_cruise["expected_vibration_g"] > vib_idle["expected_vibration_g"]
    assert 0.06 <= vib_idle["expected_vibration_g"] <= 0.14
    assert 0.14 <= vib_cruise["expected_vibration_g"] <= 0.22
    assert 0.22 <= vib_takeoff["expected_vibration_g"] <= 0.32


def test_full_physics_engine_operating_regimes():
    """
    Test the complete Rotax914PhysicsModel across 5 required operational regimes:
    1. Idle
    2. Cruise
    3. High Throttle / Takeoff
    4. High Altitude
    5. High Ambient Temperature
    """
    model = Rotax914PhysicsModel()

    # 1. Idle (Throttle 10%, 0 ft, 15°C)
    idle = model.predict_state(throttle=10.0, altitude_ft=0, ambient_temperature_c=15.0)
    assert 1400 <= idle["expected_rpm"] <= 2000
    assert idle["expected_power_kw"] < 15.0
    assert idle["expected_fuel_flow_lph"] < 7.0
    assert idle["expected_oil_pressure_bar"] >= 1.8
    assert idle["expected_vibration_g"] < 0.15

    # 2. Cruise (Throttle 65%, 10,000 ft, 15°C)
    cruise = model.predict_state(throttle=65.0, altitude_ft=10000, ambient_temperature_c=15.0)
    assert 4800 <= cruise["expected_rpm"] <= 5300
    assert 45.0 <= cruise["expected_power_kw"] <= 68.0
    assert 13.0 <= cruise["expected_fuel_flow_lph"] <= 21.0
    assert 650.0 <= cruise["expected_egt_c"] <= 780.0
    assert 100.0 <= cruise["expected_cht_c"] <= 135.0
    assert 3.0 <= cruise["expected_oil_pressure_bar"] <= 4.9

    # 3. High Throttle / Takeoff (Throttle 100%, 0 ft, 15°C)
    takeoff = model.predict_state(throttle=100.0, altitude_ft=0, ambient_temperature_c=15.0)
    assert takeoff["expected_rpm"] >= 5700.0
    assert takeoff["expected_power_kw"] >= 78.0
    assert takeoff["expected_fuel_flow_lph"] >= 24.0
    assert takeoff["expected_torque_nm"] >= 130.0

    # 4. High Altitude (Throttle 75%, 22,000 ft, -15°C)
    high_alt = model.predict_state(throttle=75.0, altitude_ft=22000, ambient_temperature_c=-15.0)
    assert high_alt["ambient_pressure_bar"] < 0.50
    assert high_alt["air_density_kgm3"] < 0.65
    assert high_alt["expected_power_kw"] > 0

    # 5. High Ambient Temperature (Throttle 65%, 2,000 ft, 42°C)
    hot_day = model.predict_state(throttle=65.0, altitude_ft=2000, ambient_temperature_c=42.0)
    std_day = model.predict_state(throttle=65.0, altitude_ft=2000, ambient_temperature_c=15.0)
    assert hot_day["expected_cht_c"] > std_day["expected_cht_c"]
    assert hot_day["expected_oil_temperature_c"] > std_day["expected_oil_temperature_c"]

    # Monotonicity checks: Throttle progression 20% -> 50% -> 80%
    s20 = model.predict_state(throttle=20.0, altitude_ft=5000, ambient_temperature_c=15.0)
    s50 = model.predict_state(throttle=50.0, altitude_ft=5000, ambient_temperature_c=15.0)
    s80 = model.predict_state(throttle=80.0, altitude_ft=5000, ambient_temperature_c=15.0)

    assert s80["expected_power_kw"] > s50["expected_power_kw"] > s20["expected_power_kw"]
    assert s80["expected_rpm"] > s50["expected_rpm"] > s20["expected_rpm"]
    assert s80["expected_fuel_flow_lph"] > s50["expected_fuel_flow_lph"] > s20["expected_fuel_flow_lph"]
    assert s80["expected_cht_c"] > s50["expected_cht_c"] > s20["expected_cht_c"]
    assert s80["expected_vibration_g"] > s50["expected_vibration_g"] > s20["expected_vibration_g"]

    # Non-negativity check across all fields
    for s in [idle, cruise, takeoff, high_alt, hot_day, s20, s50, s80]:
        for k, v in s.items():
            if isinstance(v, (int, float)) and k != "ambient_temperature_c":
                assert v >= 0.0, f"Field {k} has negative value {v}"
