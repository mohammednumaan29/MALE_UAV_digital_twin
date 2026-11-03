#!/usr/bin/env python3
"""Standalone mission simulation runner for the Rotax 914 digital twin."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.services.mission_service import mission_simulation_service


def run_mission(
    engine_id: str = "rotax914-uav-01",
    duration_hours: float = 8.0,
    altitude_ft: float = 12000.0,
    ambient_temperature_c: float = 38.0,
    throttle: float = 65.0,
    mission_type: str = "SURVEILLANCE",
) -> None:
    """Generate a mission summary using the physics-informed mission service."""
    summary = mission_simulation_service.simulate(
        engine_id=engine_id,
        duration_hours=duration_hours,
        altitude_ft=altitude_ft,
        ambient_temperature_c=ambient_temperature_c,
        throttle=throttle,
        mission_type=mission_type,
    )
    print("MISSION SIMULATION")
    print(f"ENGINE: {summary['engine_id']}")
    print(f"TYPE: {summary['mission_type']}")
    print(f"DURATION: {summary['duration_hours']} h")
    print(f"ALTITUDE: {summary['altitude_ft']} ft")
    print(f"AMBIENT: {summary['ambient_temperature_c']} C")
    print(f"THROTTLE: {summary['throttle']}%")
    print(f"HEALTH START: {summary['health_start']} / 100")
    print(f"HEALTH END: {summary['health_end']} / 100")
    print(f"DEGRADATION: {summary['predicted_degradation']}")
    print(f"MISSION RISK: {summary['mission_risk']}")
    print(f"ESTIMATED RUL: {summary['estimated_rul']} h")
    print(f"RECOMMENDATION: {summary['recommendations']}")
    print("TIMELINE SAMPLE:")
    for idx, point in enumerate(summary["timeline"][:3]):
        print(
            f"{idx + 1}: {point['timestamp']} | "
            f"RPM {point['rpm']:.0f} | "
            f"EGT {point['egt_c']:.1f} C | "
            f"CHT {point['cht_c']:.1f} C | "
            f"Oil {point['oil_temperature_c']:.1f} C | "
            f"Health {point['health_index']:.1f}"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Rotax 914 mission simulation")
    parser.add_argument("--engine-id", default="rotax914-uav-01")
    parser.add_argument("--duration-hours", type=float, default=8.0)
    parser.add_argument("--altitude-ft", type=float, default=12000.0)
    parser.add_argument("--ambient-temperature-c", type=float, default=38.0)
    parser.add_argument("--throttle", type=float, default=65.0)
    parser.add_argument("--mission-type", default="SURVEILLANCE")
    args = parser.parse_args()

    run_mission(
        engine_id=args.engine_id,
        duration_hours=args.duration_hours,
        altitude_ft=args.altitude_ft,
        ambient_temperature_c=args.ambient_temperature_c,
        throttle=args.throttle,
        mission_type=args.mission_type,
    )
