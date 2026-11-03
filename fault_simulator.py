#!/usr/bin/env python3
"""Standalone fault injector for the Rotax 914 digital twin.

This module updates the shared fault state file used by the live engine
simulator. The engine simulator remains the same; only the shared state is
changed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.config.constants import FaultCategory
from app.simulation.fault_injector import SharedFaultState


def _fault_choices() -> list[str]:
    return [fault.value for fault in FaultCategory]


def _print_state(state: dict) -> None:
    print("ACTIVE FAULT: " + state["active_fault"])
    print(f"SEVERITY: {state['target_severity_pct']:.0f}%")


def _interactive_menu() -> None:
    controller = SharedFaultState()
    current = controller.read_state()
    print("=" * 52)
    print("ROTAX 914 FAULT SIMULATOR")
    print("=" * 52)
    print(f"Current state: {current.get('active_fault', 'NORMAL')} @ {current.get('target_severity_pct', 0.0):.0f}%")
    print("1. NORMAL")
    print("2. FUEL_MIXTURE_DEGRADATION")
    print("3. OVERHEATING")
    print("4. LUBRICATION_DEGRADATION")
    print("5. ABNORMAL_VIBRATION")
    print("6. SENSOR_ANOMALY")
    print("7. CLEAR")
    print("=" * 52)

    choice = input("Select option (1-7): ").strip()
    fault_map = {
        "1": FaultCategory.NORMAL,
        "2": FaultCategory.FUEL_MIXTURE,
        "3": FaultCategory.OVERHEATING,
        "4": FaultCategory.LUBRICATION,
        "5": FaultCategory.VIBRATION,
        "6": FaultCategory.SENSOR_ANOMALY,
    }

    if choice == "7":
        state = controller.clear()
        print("FAULT CLEARED")
        _print_state(state)
        return

    selected = fault_map.get(choice)
    if selected is None:
        print("Invalid option.")
        return

    severity = 0.0 if selected == FaultCategory.NORMAL else 50.0
    if selected != FaultCategory.NORMAL:
        try:
            severity = float(input("Severity (0-100): ") or "50")
        except ValueError:
            severity = 50.0
    state = controller.set_fault(selected, severity)
    _print_state(state)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject faults into the shared Rotax 914 simulator state")
    parser.add_argument("fault_positional", nargs="?", choices=_fault_choices(), help=argparse.SUPPRESS)
    parser.add_argument("severity_positional", nargs="?", type=float, help=argparse.SUPPRESS)
    parser.add_argument("--fault", dest="fault_flag", choices=_fault_choices(), help="Fault category to activate")
    parser.add_argument("--severity", dest="severity_flag", type=float, default=50.0, help="Severity percent from 0-100")
    parser.add_argument("--clear", action="store_true", help="Reset shared fault state to NORMAL")
    args = parser.parse_args()

    controller = SharedFaultState()

    if args.clear:
        state = controller.clear()
        print("FAULT CLEARED")
        _print_state(state)
        return

    fault_name = args.fault_flag or args.fault_positional
    severity = args.severity_flag if args.fault_flag is not None else (args.severity_positional if args.severity_positional is not None else 50.0)

    if fault_name is None:
        _interactive_menu()
        return

    state = controller.set_fault(fault_name, severity)
    _print_state(state)


if __name__ == "__main__":
    main()
