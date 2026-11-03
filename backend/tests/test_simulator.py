"""
Automated tests for Real-Time Engine Simulator.
Phase 2 Verification:
- Continuous telemetry generation
- Dynamic thermal/mechanical inertia
- No unrealistic 1-second random jumping or oscillation
- Sensor measurement noise
- Mission profile progression
"""

import math
import pytest
from app.simulation.sensor_noise import SensorNoiseModel
from app.simulation.mission_profile import MissionProfile
from app.simulation.engine_simulator import EngineSimulator
from app.schemas.telemetry import TelemetryData


def test_sensor_noise_statistics_and_reproducibility():
    """Verify sensor noise zero-mean properties and seed reproducibility."""
    seed = 42
    noise_model1 = SensorNoiseModel(seed=seed)
    noise_model2 = SensorNoiseModel(seed=seed)

    base_frame = {
        "rpm": 5000.0,
        "egt_c": 720.0,
        "cht_c": 115.0,
        "oil_pressure_bar": 3.8,
        "oil_temperature_c": 92.0,
        "fuel_flow_lph": 18.0,
        "vibration_g": 0.18,
        "throttle": 65.0,
    }

    # Test seed reproducibility: identical seeds produce identical outputs
    sample1 = noise_model1.apply_noise(base_frame)
    sample2 = noise_model2.apply_noise(base_frame)
    assert sample1 == sample2

    # Test statistical properties over 500 samples
    rpm_diffs = []
    noise_model = SensorNoiseModel(seed=123)
    for _ in range(500):
        noisy = noise_model.apply_noise(base_frame)
        rpm_diffs.append(noisy["rpm"] - base_frame["rpm"])

    mean_rpm_diff = sum(rpm_diffs) / len(rpm_diffs)
    # Mean should be very close to zero (within 3 standard errors: 3 * (4.0 / sqrt(500)) ~ 0.54)
    assert abs(mean_rpm_diff) < 1.0


def test_mission_profile_progression():
    """Verify mission profile keyframes and continuous interpolation."""
    profile = MissionProfile()

    # 1. Idle segment (0 to 30s)
    f0 = profile.get_flight_condition(0.0)
    f15 = profile.get_flight_condition(15.0)
    f30 = profile.get_flight_condition(30.0)

    assert f0["throttle"] == 15.0
    assert f0["altitude_ft"] == 0.0
    assert f15["throttle"] == 15.0
    assert f30["throttle"] == 15.0
    assert f0["phase"] == "IDLE"

    # 2. Takeoff segment (35 to 60s)
    f40 = profile.get_flight_condition(40.0)
    assert f40["throttle"] == 100.0
    assert f40["phase"] == "TAKEOFF"

    # 3. Climb segment (60 to 150s)
    f100 = profile.get_flight_condition(100.0)
    assert f100["altitude_ft"] > 2000.0
    assert f100["phase"] == "CLIMB"

    # 4. Cruise segment (160s+)
    f200 = profile.get_flight_condition(200.0)
    assert f200["throttle"] == 65.0
    assert f200["altitude_ft"] == 10000.0
    assert f200["phase"] == "CRUISE"

    # Smooth continuous progression (no abrupt negative slopes in climb)
    altitudes = [profile.get_flight_condition(t)["altitude_ft"] for t in range(30, 160, 5)]
    for i in range(len(altitudes) - 1):
        assert altitudes[i + 1] >= altitudes[i]


def test_dynamic_inertia_smoothness():
    """
    Verify engine simulator exhibits realistic mechanical & thermal inertia.
    RPM must NOT jump instantaneously; temperatures must evolve slowly.
    """
    # Simulator with zero sensor noise to test raw ODE physics integration
    noise_model = SensorNoiseModel(enabled=False)
    sim = EngineSimulator(dt_seconds=1.0, noise_model=noise_model)

    # Initial state is ground idle
    assert sim.current_state["throttle"] == 15.0
    assert sim.current_state["rpm"] < 2200.0

    # Run for 60 seconds (covering idle -> takeoff transition at t=30s)
    history = []
    for _ in range(60):
        frame = sim.step()
        history.append(frame)

    # Check that at t=31, 32, 33s (takeoff throttle application), RPM ramps smoothly:
    # Under 1.5s time constant, max single-second RPM delta should be bounded (~1000-1800 RPM/s max)
    rpm_deltas = [
        abs(history[i + 1]["rpm"] - history[i]["rpm"])
        for i in range(len(history) - 1)
    ]
    max_rpm_delta = max(rpm_deltas)
    assert max_rpm_delta < 2200.0, f"RPM jumped too fast: {max_rpm_delta} RPM/s"

    # Verify CHT changes slowly (thermal inertia)
    # Liquid-cooled CHT has tau = 35s, so delta per second should be < 5°C/s
    cht_deltas = [
        abs(history[i + 1]["cht_c"] - history[i]["cht_c"])
        for i in range(len(history) - 1)
    ]
    max_cht_delta = max(cht_deltas)
    assert max_cht_delta < 4.0, f"CHT changed too fast: {max_cht_delta} °C/s"

    # Verify Oil Temperature changes slowly (tau = 60s)
    oil_deltas = [
        abs(history[i + 1]["oil_temperature_c"] - history[i]["oil_temperature_c"])
        for i in range(len(history) - 1)
    ]
    max_oil_delta = max(oil_deltas)
    assert max_oil_delta < 2.5, f"Oil temp changed too fast: {max_oil_delta} °C/s"


def test_no_unrealistic_one_second_oscillation():
    """
    Verify steady-state stability during cruise:
    In level cruise at constant throttle, parameters must remain stable with small noise.
    """
    profile = MissionProfile(keyframes=[
        (0.0, 65.0, 10000.0, -4.8),
        (200.0, 65.0, 10000.0, -4.8),
    ])
    sim = EngineSimulator(dt_seconds=1.0, mission_profile=profile, seed=123)

    # Let the engine settle for 100 steps
    for _ in range(100):
        sim.step()

    # Collect 30 cruise samples
    samples = [sim.step() for _ in range(30)]

    rpms = [s["rpm"] for s in samples]
    egts = [s["egt_c"] for s in samples]
    chts = [s["cht_c"] for s in samples]
    oil_pressures = [s["oil_pressure_bar"] for s in samples]

    # Standard deviation over steady cruise should strictly reflect sensor noise, not wild oscillation
    rpm_mean = sum(rpms) / len(rpms)
    rpm_std = math.sqrt(sum((x - rpm_mean) ** 2 for x in rpms) / len(rpms))
    assert rpm_std < 15.0, f"Unrealistic RPM oscillation during steady cruise: std={rpm_std}"

    cht_mean = sum(chts) / len(chts)
    cht_std = math.sqrt(sum((x - cht_mean) ** 2 for x in chts) / len(chts))
    assert cht_std < 2.0, f"Unrealistic CHT oscillation: std={cht_std}"

    oil_mean = sum(oil_pressures) / len(oil_pressures)
    oil_std = math.sqrt(sum((x - oil_mean) ** 2 for x in oil_pressures) / len(oil_pressures))
    assert oil_std < 0.10, f"Unrealistic oil pressure oscillation: std={oil_std}"


def test_configurable_timestep():
    """Verify simulator operates reliably across dt = 0.1s, 0.5s, and 1.0s."""
    for dt in [0.1, 0.5, 1.0]:
        sim = EngineSimulator(dt_seconds=dt, seed=42)
        # Advance 10 steps
        for _ in range(10):
            frame = sim.step()
            assert frame["rpm"] > 0
            assert frame["oil_pressure_bar"] > 0
            assert frame["egt_c"] > 0
            assert frame["power_kw"] >= 0


def test_telemetry_schema_validation():
    """Verify generated simulator frames validate against Pydantic TelemetryData schema."""
    sim = EngineSimulator(dt_seconds=1.0, seed=99)
    for _ in range(10):
        frame = sim.step()
        validated = TelemetryData(**frame)
        assert validated.rpm > 0
        assert validated.altitude_ft >= 0.0
        assert validated.oil_pressure_bar > 0.0
        assert 0.0 <= validated.throttle <= 100.0
