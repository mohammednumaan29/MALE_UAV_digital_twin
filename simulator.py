#!/usr/bin/env python3
"""Standalone Rotax 914 simulator runner.

Runs the existing engine simulator and reads the shared fault state file to
apply decoupled fault injections without replacing the underlying simulator.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.simulation.engine_simulator import EngineSimulator
from app.simulation.fault_injector import SharedFaultState
from app.simulation.sensor_noise import SensorNoiseModel

BACKEND_TELEMETRY_URL = "http://localhost:8000/api/telemetry"


def post_telemetry(frame: dict) -> None:
    """Send the latest simulator frame to the FastAPI telemetry endpoint."""
    payload = {
        "engine_id": "rotax914-uav-01",
        "timestamp": frame.get("timestamp"),
        "rpm": float(frame["rpm"]),
        "egt_c": float(frame["egt_c"]),
        "cht_c": float(frame["cht_c"]),
        "oil_pressure_bar": float(frame["oil_pressure_bar"]),
        "oil_temperature_c": float(frame["oil_temperature_c"]),
        "fuel_flow_lph": float(frame["fuel_flow_lph"]),
        "vibration_g": float(frame["vibration_g"]),
        "altitude_ft": float(frame["altitude_ft"]),
        "ambient_temperature_c": float(frame["ambient_temperature_c"]),
        "throttle": float(frame["throttle"]),
        "engine_load": float(frame.get("engine_load", 0.0)),
        "power_kw": float(frame.get("power_kw", 0.0)),
        "active_fault": frame.get("active_fault", "NORMAL"),
        "fault_severity": float(frame.get("fault_severity", 0.0)),
    }

    request = Request(
        BACKEND_TELEMETRY_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=5) as response:
            response.read()
    except (HTTPError, URLError, OSError) as exc:
        print(f"Unable to send telemetry to backend: {exc}", file=sys.stderr)


def run_simulation(duration_s: float = 60.0, dt_s: float = 1.0, realtime: bool = True) -> None:
    """Run the engine simulator and display live telemetry."""
    sim = EngineSimulator(
        dt_seconds=dt_s,
        noise_model=SensorNoiseModel(enabled=True),
        fault_controller=SharedFaultState(),
    )

    print("ENGINE SIMULATOR RUNNING")
    print("Press Ctrl+C to stop")
    print("-" * 88)

    try:
        while True:
            if duration_s is not None and sim.elapsed_time_s >= duration_s:
                break

            frame = sim.step()
            post_telemetry(frame)
            fault_name = frame.get("active_fault", "NORMAL")
            severity_pct = float(frame.get("fault_severity_pct", 0.0))

            print(
                f"RPM: {frame['rpm']:.0f} | "
                f"EGT: {frame['egt_c']:.1f} C | "
                f"CHT: {frame['cht_c']:.1f} C | "
                f"Oil Pressure: {frame['oil_pressure_bar']:.2f} bar | "
                f"Oil Temperature: {frame['oil_temperature_c']:.1f} C | "
                f"Fuel Flow: {frame['fuel_flow_lph']:.1f} L/h | "
                f"Vibration: {frame['vibration_g']:.2f} g | "
                f"Altitude: {frame['altitude_ft']:.0f} ft | "
                f"Ambient Temperature: {frame['ambient_temperature_c']:.1f} C | "
                f"Throttle: {frame['throttle']:.0f}%"
            )
            if fault_name != "NORMAL":
                print(f"ACTIVE FAULT: {fault_name}")
                print(f"SEVERITY: {severity_pct:.0f}%")
            print("-" * 88)

            if realtime:
                time.sleep(dt_s)
    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Rotax 914 engine telemetry simulator")
    parser.add_argument("--duration", type=float, default=300.0, help="Run time in seconds (default: 300)")
    parser.add_argument("--dt", type=float, default=1.0, help="Simulation timestep in seconds")
    parser.add_argument("--fast", action="store_true", help="Run without real-time sleep")
    args = parser.parse_args()

    run_simulation(duration_s=args.duration, dt_s=args.dt, realtime=not args.fast)
