"""
Automated tests for Fault Injection & Physical Degradation subsystem.
Phase 3 Verification:
- Shared fault state IPC
- Physical degradation effects for all 5 fault categories
- Gradual dynamic transition onset and recovery
"""

import tempfile
from pathlib import Path
import pytest
from app.config.constants import FaultCategory
from app.simulation.fault_effects import apply_fault_effects
from app.simulation.fault_injector import SharedFaultState
from app.simulation.engine_simulator import EngineSimulator
from app.simulation.sensor_noise import SensorNoiseModel


@pytest.fixture
def temp_fault_state():
    """Create a temporary fault state file for isolated testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "test_fault_state.json"
        controller = SharedFaultState(state_file=state_file)
        yield controller


def test_shared_fault_state_persistence(temp_fault_state):
    """Verify atomic write, read, and reset of shared fault state."""
    controller = temp_fault_state

    # Initially healthy
    initial = controller.read_state()
    assert initial["active_fault"] == FaultCategory.NORMAL.value
    assert initial["target_severity"] == 0.0

    # Inject Overheating 60%
    updated = controller.set_fault(FaultCategory.OVERHEATING, 60.0)
    assert updated["active_fault"] == FaultCategory.OVERHEATING.value
    assert updated["target_severity"] == 0.60
    assert updated["target_severity_pct"] == 60.0

    # Read again
    read_back = controller.read_state()
    assert read_back["active_fault"] == FaultCategory.OVERHEATING.value
    assert read_back["target_severity"] == 0.60

    # Reset
    cleared = controller.clear()
    assert cleared["active_fault"] == FaultCategory.NORMAL.value
    assert cleared["target_severity"] == 0.0


def test_fault_effects_fuel_mixture():
    """Verify Carburetor / Fuel-Mixture degradation physical effects."""
    base = {
        "rpm": 5100.0,
        "egt_c": 720.0,
        "cht_c": 110.0,
        "oil_pressure_bar": 3.8,
        "oil_temperature_c": 92.0,
        "fuel_flow_lph": 18.5,
        "vibration_g": 0.17,
        "power_kw": 55.0,
    }

    # 60% severity
    deg = apply_fault_effects(base, FaultCategory.FUEL_MIXTURE, severity=0.60)
    assert deg["fuel_flow_lph"] < base["fuel_flow_lph"]          # Leans out
    assert deg["egt_c"] > base["egt_c"]                          # Lean burn increases EGT
    assert deg["cht_c"] > base["cht_c"]                          # Combustion temp rises
    assert deg["power_kw"] < base["power_kw"]                    # Power drops
    assert deg["rpm"] < base["rpm"]                              # RPM droops
    assert deg["vibration_g"] > base["vibration_g"]              # Roughness increases
    assert deg["active_fault"] == FaultCategory.FUEL_MIXTURE.value


def test_fault_effects_overheating():
    """Verify Overheating thermal degradation physical effects."""
    base = {
        "rpm": 5100.0,
        "egt_c": 720.0,
        "cht_c": 110.0,
        "oil_pressure_bar": 3.8,
        "oil_temperature_c": 92.0,
        "fuel_flow_lph": 18.5,
        "vibration_g": 0.17,
        "power_kw": 55.0,
    }

    # 60% severity overheating
    deg = apply_fault_effects(base, FaultCategory.OVERHEATING, severity=0.60)
    assert deg["cht_c"] > base["cht_c"] + 20.0                   # CHT rises strongly
    assert deg["egt_c"] > base["egt_c"]                          # EGT rises
    assert deg["oil_temperature_c"] > base["oil_temperature_c"]  # Oil temp rises
    assert deg["oil_pressure_bar"] < base["oil_pressure_bar"]    # Oil pressure drops (hot thin oil)
    assert deg["power_kw"] < base["power_kw"]                    # Power decreases slightly
    assert deg["active_fault"] == FaultCategory.OVERHEATING.value


def test_fault_effects_lubrication():
    """Verify Lubrication degradation physical effects."""
    base = {
        "rpm": 5100.0,
        "egt_c": 720.0,
        "cht_c": 110.0,
        "oil_pressure_bar": 3.8,
        "oil_temperature_c": 92.0,
        "fuel_flow_lph": 18.5,
        "vibration_g": 0.17,
        "power_kw": 55.0,
    }

    # 70% severity lubrication fault
    deg = apply_fault_effects(base, FaultCategory.LUBRICATION, severity=0.70)
    assert deg["oil_pressure_bar"] < base["oil_pressure_bar"] - 1.0  # Massive oil pressure drop
    assert deg["oil_temperature_c"] > base["oil_temperature_c"]     # High friction heats oil
    assert deg["vibration_g"] > base["vibration_g"] + 0.08          # Bearing rumble / vibration
    assert deg["rpm"] < base["rpm"]                                 # RPM droop from friction
    assert deg["power_kw"] < base["power_kw"]                       # Mechanical loss
    assert deg["active_fault"] == FaultCategory.LUBRICATION.value


def test_fault_effects_abnormal_vibration():
    """Verify Abnormal Mechanical Vibration physical effects."""
    base = {
        "rpm": 5100.0,
        "egt_c": 720.0,
        "cht_c": 110.0,
        "oil_pressure_bar": 3.8,
        "oil_temperature_c": 92.0,
        "fuel_flow_lph": 18.5,
        "vibration_g": 0.17,
        "power_kw": 55.0,
    }

    deg = apply_fault_effects(base, FaultCategory.VIBRATION, severity=0.80)
    assert deg["vibration_g"] > base["vibration_g"] + 0.30       # Dramatic vibration surge
    assert deg["power_kw"] <= base["power_kw"]
    assert deg["active_fault"] == FaultCategory.VIBRATION.value


def test_gradual_fault_onset_and_recovery(temp_fault_state):
    """
    Verify the engine simulator responds gradually to fault injection
    and recovers smoothly when restored to NORMAL.
    """
    controller = temp_fault_state
    noise_model = SensorNoiseModel(enabled=False)
    sim = EngineSimulator(dt_seconds=1.0, noise_model=noise_model, fault_controller=controller)

    # Let engine stabilize at baseline (first 10 seconds)
    for _ in range(10):
        sim.step()

    baseline_cht = sim.current_state["cht_c"]
    baseline_egt = sim.current_state["egt_c"]

    # Inject OVERHEATING @ 60%
    controller.set_fault(FaultCategory.OVERHEATING, 60.0)

    # Step 1 immediately after fault injection:
    # Must NOT have jumped to full 60% severity instantly!
    f1 = sim.step()
    assert 0.0 < f1["fault_severity"] < 0.35, f"Fault jumped too fast: {f1['fault_severity']}"

    # Advance 15 seconds: severity should smoothly ramp towards 0.60
    history_heat = []
    for _ in range(15):
        history_heat.append(sim.step())

    peak_frame = history_heat[-1]
    assert 0.55 <= peak_frame["fault_severity"] <= 0.61
    assert peak_frame["cht_c"] > baseline_cht + 15.0

    # Clear fault back to NORMAL
    controller.clear()

    # Verify gradual decay back to baseline over 15 seconds
    history_recovery = []
    for _ in range(18):
        history_recovery.append(sim.step())

    recovered_frame = history_recovery[-1]
    assert recovered_frame["fault_severity"] < 0.05
    assert recovered_frame["active_fault"] == FaultCategory.NORMAL.value
