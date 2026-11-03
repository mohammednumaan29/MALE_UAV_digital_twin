"""
Independent Fault Injector Controller and Shared State Abstraction.
Allows operators, test scripts, or external terminals to inject physical engine degradations
independently of the running engine simulator.

Classification: [Decoupled Fault Controller]
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from app.config.constants import FaultCategory

# Location of shared IPC fault state file
DEFAULT_FAULT_STATE_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "fault_state.json"


class SharedFaultState:
    """
    Atomic shared state abstraction for decoupled fault control.
    Supports inter-process communication between simulator and fault controller.
    """

    def __init__(self, state_file: Path | str | None = None):
        self.state_file = Path(state_file or DEFAULT_FAULT_STATE_FILE)
        # Ensure parent directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        # Initialize default healthy state if file does not exist
        if not self.state_file.exists():
            self.set_fault(FaultCategory.NORMAL, 0.0)

    def read_state(self) -> Dict[str, Any]:
        """Read the current active fault and target severity."""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass

        # Fallback to healthy baseline if read fails
        return {
            "active_fault": FaultCategory.NORMAL.value,
            "target_severity": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def set_fault(self, fault: FaultCategory | str, severity_pct: float) -> Dict[str, Any]:
        """
        Atomically set a new fault and target severity.

        Args:
            fault: Fault category.
            severity_pct: Severity between 0.0% and 100.0%.
        """
        f_cat = FaultCategory(fault) if isinstance(fault, str) else fault
        clamped_pct = max(0.0, min(100.0, float(severity_pct)))
        severity_fraction = clamped_pct / 100.0

        state = {
            "active_fault": f_cat.value,
            "target_severity": round(severity_fraction, 4),
            "target_severity_pct": round(clamped_pct, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Atomic write: write to temp file then replace
        temp_file = self.state_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        temp_file.replace(self.state_file)

        return state

    def clear(self) -> Dict[str, Any]:
        """Reset fault to NORMAL at 0% severity."""
        return self.set_fault(FaultCategory.NORMAL, 0.0)


def interactive_menu(shared_state: SharedFaultState) -> None:
    """Run interactive terminal menu for operator fault injection."""
    current = shared_state.read_state()
    print("\n" + "=" * 55)
    print("ROTAX 914 FAULT INJECTION CONTROLLER")
    print("=" * 55)
    print(f"Current State: {current.get('active_fault', 'NORMAL')} @ {current.get('target_severity_pct', 0.0)}%")
    print("-" * 55)
    print("1. NORMAL")
    print("2. FUEL_MIXTURE_DEGRADATION")
    print("3. OVERHEATING")
    print("4. LUBRICATION_DEGRADATION")
    print("5. ABNORMAL_VIBRATION")
    print("6. EXIT")
    print("=" * 55)

    try:
        choice = input("Select option (1-6): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        return

    fault_map = {
        "1": FaultCategory.NORMAL,
        "2": FaultCategory.FUEL_MIXTURE,
        "3": FaultCategory.OVERHEATING,
        "4": FaultCategory.LUBRICATION,
        "5": FaultCategory.VIBRATION,
    }

    if choice == "6":
        print("Exiting fault injector.")
        return

    if choice not in fault_map:
        print(f"Invalid option '{choice}'.")
        return

    selected_fault = fault_map[choice]

    if selected_fault == FaultCategory.NORMAL:
        severity = 0.0
    else:
        try:
            sev_input = input("Severity (0–100): ").strip()
            severity = float(sev_input)
            severity = max(0.0, min(100.0, severity))
        except ValueError:
            print("Invalid severity. Using 50%.")
            severity = 50.0

    state = shared_state.set_fault(selected_fault, severity)
    print("\n" + "*" * 55)
    print(f"INJECTED: {state['active_fault']} at {state['target_severity_pct']}% severity")
    print("*" * 55 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rotax 914 Fault Injector CLI")
    parser.add_argument("--fault", type=str, choices=[f.value for f in FaultCategory], help="Fault category to inject")
    parser.add_argument("--severity", type=float, default=50.0, help="Fault severity percentage (0-100)")
    parser.add_argument("--clear", action="store_true", help="Clear fault back to NORMAL")
    args = parser.parse_args()

    controller = SharedFaultState()

    if args.clear:
        res = controller.clear()
        print(f"Fault cleared: {res['active_fault']} ({res['target_severity_pct']}%)")
    elif args.fault:
        res = controller.set_fault(args.fault, args.severity)
        print(f"Injected: {res['active_fault']} at {res['target_severity_pct']}%")
    else:
        interactive_menu(controller)
