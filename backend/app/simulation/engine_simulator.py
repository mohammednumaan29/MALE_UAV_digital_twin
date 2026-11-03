"""
Real-Time Continuous Aero-Piston Engine Simulator.
Simulates dynamic thermal/mechanical inertia, time-step integration,
sensor measurement uncertainty, and continuous telemetry generation.

Classification: [Dynamic Telemetry Simulator]
References:
- Phase 2 Implementation Specification.
- First-Order Dynamic State ODEs.
"""

import sys
import time
import math
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, Generator

from app.physics.engine_model import Rotax914PhysicsModel
from app.simulation.sensor_noise import SensorNoiseModel
from app.simulation.mission_profile import MissionProfile
from app.simulation.fault_effects import apply_fault_effects
from app.simulation.fault_injector import SharedFaultState
from app.config.constants import FaultCategory


class EngineSimulator:
    """
    Continuous dynamic simulation engine for the Rotax 914 aero-piston propulsion system.
    Integrates dynamic state equations with physical inertia to produce smooth, non-oscillatory telemetry.
    """

    # Physical time constants for first-order dynamic response (in seconds)
    # dx/dt = (x_target - x) / tau
    TAU_RPM: float = 1.5           # Rotational inertia (crankshaft, flywheel, reduction gear, propeller)
    TAU_EGT: float = 2.5           # Exhaust gas thermocouple & combustion heat transition
    TAU_CHT: float = 45.0          # Cylinder head & coolant fluid thermal capacitance
    TAU_OIL_TEMP: float = 60.0     # Dry-sump oil volume (~3 L) & external cooler thermal inertia
    TAU_OIL_PRESS: float = 0.5     # Hydrodynamic pump pressure response
    TAU_FUEL_FLOW: float = 0.8     # Carburetor fuel metering & manifold transport delay
    TAU_VIBRATION: float = 0.5     # Structural vibration tracking
    TAU_POWER: float = 1.0         # Mechanical power tracking
    TAU_FAULT: float = 4.0         # Dynamic inertia for gradual fault onset and recovery

    def __init__(
        self,
        dt_seconds: float = 1.0,
        mission_profile: MissionProfile | None = None,
        noise_model: SensorNoiseModel | None = None,
        physics_model: Rotax914PhysicsModel | None = None,
        fault_controller: SharedFaultState | None = None,
        seed: int | None = None,
    ):
        """
        Initialize the real-time engine simulator.

        Args:
            dt_seconds: Time-step duration (e.g. 0.1, 0.5, 1.0 second).
            mission_profile: MissionProfile instance for flight conditions.
            noise_model: SensorNoiseModel instance for transducer measurement noise.
            physics_model: Rotax914PhysicsModel virtual engine instance.
            fault_controller: SharedFaultState instance for decoupled IPC fault injection.
            seed: Optional random seed for reproducible runs.
        """
        self.dt = max(0.01, float(dt_seconds))
        self.mission_profile = mission_profile or MissionProfile()
        self.noise_model = noise_model or SensorNoiseModel(seed=seed)
        self.physics = physics_model or Rotax914PhysicsModel()
        self.fault_controller = fault_controller or SharedFaultState()

        # Dynamic fault tracking state
        self.current_fault_type: FaultCategory = FaultCategory.NORMAL
        self.current_fault_severity: float = 0.0

        # Elapsed simulation time in seconds
        self.elapsed_time_s: float = 0.0

        # Initialize dynamic state at ground idle
        self._initialize_state()

    def _initialize_state(self) -> None:
        """Set initial dynamic state to ground idle equilibrium."""
        # Evaluate initial flight condition at t=0
        fc = self.mission_profile.get_flight_condition(0.0)
        target = self.physics.predict_state(
            throttle=fc["throttle"],
            altitude_ft=fc["altitude_ft"],
            ambient_temperature_c=fc["ambient_temperature_c"]
        )

        self.current_state: Dict[str, float] = {
            "rpm": target["expected_rpm"],
            "egt_c": target["expected_egt_c"],
            "cht_c": target["expected_cht_c"],
            "oil_pressure_bar": target["expected_oil_pressure_bar"],
            "oil_temperature_c": target["expected_oil_temperature_c"],
            "fuel_flow_lph": target["expected_fuel_flow_lph"],
            "vibration_g": target["expected_vibration_g"],
            "power_kw": target["expected_power_kw"],
            "engine_load": target["engine_load"],
            "throttle": fc["throttle"],
            "altitude_ft": fc["altitude_ft"],
            "ambient_temperature_c": fc["ambient_temperature_c"],
        }

    def reset(self, seed: int | None = None) -> None:
        """Reset the simulation back to t=0."""
        self.elapsed_time_s = 0.0
        if seed is not None:
            self.noise_model.set_seed(seed)
        self._initialize_state()

    def _apply_inertia(self, current_val: float, target_val: float, tau: float) -> float:
        """
        Step a dynamic variable forward by dt using first-order low-pass filter:
        x_{new} = x_{old} + (1 - exp(-dt / tau)) * (x_{target} - x_{old})
        """
        if tau <= 0.001:
            return target_val
        alpha = 1.0 - math.exp(-self.dt / tau)
        return current_val + alpha * (target_val - current_val)

    def step(self) -> Dict[str, Any]:
        """
        Advance the simulation forward by one timestep (dt).

        Returns:
            Dict containing complete continuous telemetry sample.
        """
        # 1. Evaluate current boundary conditions from mission profile
        fc = self.mission_profile.get_flight_condition(self.elapsed_time_s)
        throttle = fc["throttle"]
        altitude_ft = fc["altitude_ft"]
        ambient_temp_c = fc["ambient_temperature_c"]

        # 2. Evaluate steady-state physics targets for these operating conditions
        # Pass current dynamic RPM as override to physics model for coupled internal states
        steady_targets = self.physics.predict_state(
            throttle=throttle,
            altitude_ft=altitude_ft,
            ambient_temperature_c=ambient_temp_c
        )

        # 3. Integrate dynamic state using physical time constants
        new_rpm = self._apply_inertia(self.current_state["rpm"], steady_targets["expected_rpm"], self.TAU_RPM)
        new_egt = self._apply_inertia(self.current_state["egt_c"], steady_targets["expected_egt_c"], self.TAU_EGT)
        new_cht = self._apply_inertia(self.current_state["cht_c"], steady_targets["expected_cht_c"], self.TAU_CHT)
        new_oil_temp = self._apply_inertia(
            self.current_state["oil_temperature_c"],
            steady_targets["expected_oil_temperature_c"],
            self.TAU_OIL_TEMP
        )
        new_oil_press = self._apply_inertia(
            self.current_state["oil_pressure_bar"],
            steady_targets["expected_oil_pressure_bar"],
            self.TAU_OIL_PRESS
        )
        new_fuel = self._apply_inertia(
            self.current_state["fuel_flow_lph"],
            steady_targets["expected_fuel_flow_lph"],
            self.TAU_FUEL_FLOW
        )
        new_vib = self._apply_inertia(
            self.current_state["vibration_g"],
            steady_targets["expected_vibration_g"],
            self.TAU_VIBRATION
        )
        new_power = self._apply_inertia(
            self.current_state["power_kw"],
            steady_targets["expected_power_kw"],
            self.TAU_POWER
        )
        new_load = self._apply_inertia(
            self.current_state["engine_load"],
            steady_targets["engine_load"],
            self.TAU_RPM
        )

        # Update internal state
        self.current_state = {
            "rpm": new_rpm,
            "egt_c": new_egt,
            "cht_c": new_cht,
            "oil_pressure_bar": new_oil_press,
            "oil_temperature_c": new_oil_temp,
            "fuel_flow_lph": new_fuel,
            "vibration_g": new_vib,
            "power_kw": new_power,
            "engine_load": new_load,
            "throttle": throttle,
            "altitude_ft": altitude_ft,
            "ambient_temperature_c": ambient_temp_c,
        }

        # 4. Check for active injected faults via shared IPC controller
        fault_info = self.fault_controller.read_state()
        target_fault_str = fault_info.get("active_fault", FaultCategory.NORMAL.value)
        target_sev = float(fault_info.get("target_severity", 0.0))

        try:
            target_fault = FaultCategory(target_fault_str)
        except ValueError:
            target_fault = FaultCategory.NORMAL

        if target_fault != FaultCategory.NORMAL:
            self.current_fault_type = target_fault

        # Dynamic fault inertia: evolve effective severity gradually towards target
        self.current_fault_severity = self._apply_inertia(
            self.current_fault_severity,
            target_sev,
            self.TAU_FAULT
        )

        # If severity has decayed to zero when returning to NORMAL, reset type
        if self.current_fault_severity < 0.008 and target_fault == FaultCategory.NORMAL:
            self.current_fault_severity = 0.0
            self.current_fault_type = FaultCategory.NORMAL

        # 5. Apply physical degradation effects
        degraded_state = apply_fault_effects(
            base_state=self.current_state,
            fault_type=self.current_fault_type,
            severity=self.current_fault_severity
        )

        # 6. Generate timestamp
        sim_timestamp = datetime.now(timezone.utc).isoformat()

        # 7. Apply sensor noise
        raw_telemetry = {
            "timestamp": sim_timestamp,
            "elapsed_time_s": round(self.elapsed_time_s, 1),
            "mission_phase": fc["phase"],
            **degraded_state,
            "active_fault": self.current_fault_type.value,
            "fault_severity": round(self.current_fault_severity, 3),
            "fault_severity_pct": round(self.current_fault_severity * 100.0, 1),
        }
        noisy_telemetry = self.noise_model.apply_noise(raw_telemetry)

        # Increment simulation clock
        self.elapsed_time_s += self.dt

        return noisy_telemetry

    def generate_stream(self, max_seconds: float | None = None) -> Generator[Dict[str, Any], None, None]:
        """
        Generator yielding real-time telemetry frames continuously.
        """
        while True:
            if max_seconds is not None and self.elapsed_time_s >= max_seconds:
                break
            yield self.step()


def run_standalone_simulation(
    duration_s: float = 60.0,
    dt_s: float = 1.0,
    realtime: bool = True
) -> None:
    """
    Run continuous terminal telemetry stream.
    """
    sim = EngineSimulator(dt_seconds=dt_s)

    header = (
        f"{'TIME(s)':<7} | {'PHASE':<8} | {'THROT%':<6} | {'ALT(ft)':<7} | {'RPM':<5} | "
        f"{'PWR(kW)':<7} | {'EGT(C)':<6} | {'CHT(C)':<6} | {'OIL(bar)':<8} | {'OIL(C)':<6} | "
        f"{'FF(L/h)':<7} | {'VIB(g)':<6} | {'ACTIVE_FAULT':<14} | {'SEV%':<5}"
    )
    separator = "-" * len(header)

    print("\n" + "=" * len(header))
    print("ROTAX 914 REAL-TIME ENGINE TELEMETRY SIMULATOR (MALE UAV)")
    print(f"Time-step: {dt_s}s | Duration: {duration_s}s | Real-time: {realtime}")
    print("=" * len(header))
    print(header)
    print(separator)

    try:
        for frame in sim.generate_stream(max_seconds=duration_s):
            line = (
                f"{frame['elapsed_time_s']:<7.1f} | "
                f"{frame['mission_phase']:<8} | "
                f"{frame['throttle']:<6.1f} | "
                f"{frame['altitude_ft']:<7.0f} | "
                f"{frame['rpm']:<5} | "
                f"{frame['power_kw']:<7.1f} | "
                f"{frame['egt_c']:<6.1f} | "
                f"{frame['cht_c']:<6.1f} | "
                f"{frame['oil_pressure_bar']:<8.2f} | "
                f"{frame['oil_temperature_c']:<6.1f} | "
                f"{frame['fuel_flow_lph']:<7.1f} | "
                f"{frame['vibration_g']:<6.3f} | "
                f"{frame.get('active_fault', 'NORMAL'):<14} | "
                f"{frame.get('fault_severity_pct', 0.0):<5.1f}"
            )
            print(line)
            sys.stdout.flush()

            if realtime:
                time.sleep(dt_s)

    except KeyboardInterrupt:
        print("\n[Simulator stopped by user]")

    print(separator)
    print(f"Simulation completed ({sim.elapsed_time_s:.1f} simulated seconds).\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rotax 914 Real-Time Aero-Engine Telemetry Simulator")
    parser.add_argument("--duration", type=float, default=60.0, help="Simulation duration in seconds (default: 60)")
    parser.add_argument("--dt", type=float, default=1.0, help="Simulation timestep in seconds (default: 1.0)")
    parser.add_argument("--fast", action="store_true", help="Run in fast-forward mode (no real-time sleep)")
    args = parser.parse_args()

    run_standalone_simulation(
        duration_s=args.duration,
        dt_s=args.dt,
        realtime=not args.fast
    )
