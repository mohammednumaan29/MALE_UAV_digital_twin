"""
Engine Constants, Subsystem Identifiers, Fault Categories, and System Disclaimers.
Target Engine: Rotax 914-inspired Turbocharged Aero-Piston Engine (MALE UAV Propulsion).
"""

from enum import Enum
from typing import Dict, List


# -----------------------------------------------------------------------------
# System Disclaimer
# -----------------------------------------------------------------------------
SYSTEM_DISCLAIMER: str = (
    "This software is an engineering prototype and research Digital Twin platform. "
    "It MUST NOT claim aircraft certification, guaranteed RUL, exact component diagnosis, "
    "or flight safety certification."
)


# -----------------------------------------------------------------------------
# Engine Baseline Specifications (Rotax 914 F Reference)
# -----------------------------------------------------------------------------
ENGINE_DISPLACEMENT_L: float = 1.2112           # 1211.2 cc (1.2112 liters)
ENGINE_CYLINDERS: int = 4                       # 4-cylinder, 4-stroke boxer
ENGINE_STROKES: int = 4                         # 4-stroke
COMPRESSION_RATIO: float = 9.0                  # 9.0:1

MAX_CONTINUOUS_RPM: float = 5500.0              # Max continuous RPM
TAKEOFF_RPM: float = 5800.0                     # Max takeoff RPM (5 min limit)
IDLE_RPM: float = 1400.0                        # Nominal idle RPM

MAX_CONTINUOUS_POWER_KW: float = 73.5           # 100 HP @ 5500 RPM
TAKEOFF_POWER_KW: float = 84.5                  # 115 HP @ 5800 RPM (turbo boosted)

PROPELLER_GEAR_RATIO: float = 2.43              # Integrated reduction gearbox ratio (2.43:1)

# Normal Operational Sensor Envelopes
EGT_NORMAL_C: float = 750.0                     # Nominal EGT (°C)
EGT_MAX_C: float = 950.0                        # Max permissible continuous EGT (°C)
CHT_NORMAL_C: float = 110.0                     # Nominal liquid-cooled CHT (°C)
CHT_MAX_C: float = 135.0                        # Max permissible CHT (°C)
OIL_TEMP_NORMAL_C: float = 95.0                 # Nominal oil temperature (°C)
OIL_TEMP_MAX_C: float = 130.0                   # Max oil temperature (°C)
OIL_PRESS_NORMAL_BAR: float = 3.5               # Nominal oil pressure (bar)
OIL_PRESS_MIN_BAR: float = 1.5                  # Minimum permissible oil pressure (bar)
OIL_PRESS_MAX_BAR: float = 5.0                  # Maximum normal oil pressure (bar)
VIBRATION_BASELINE_G: float = 0.15              # Baseline mechanical vibration (g RMS)


# -----------------------------------------------------------------------------
# Engine Subsystems
# -----------------------------------------------------------------------------
class EngineSubsystem(str, Enum):
    CYLINDERS = "Cylinders"
    CYLINDER_HEADS = "Cylinder heads"
    PISTONS = "Pistons"
    CONNECTING_RODS = "Connecting rods"
    CRANKSHAFT = "Crankshaft"
    BEARINGS = "Bearings"
    FUEL_CARBURETOR = "Carburetor / fuel-mixture degradation"
    INTAKE_SYSTEM = "Intake system"
    EXHAUST_SYSTEM = "Exhaust system"
    TURBOCHARGER = "Turbocharger"
    COOLING_SYSTEM = "Cooling system"
    LUBRICATION_SYSTEM = "Lubrication system"
    OIL_SYSTEM = "Oil tank/pump/filter"
    REDUCTION_GEARBOX = "Reduction gearbox"
    ENGINE_MOUNTING = "Engine mounting / mechanical region"


# -----------------------------------------------------------------------------
# Fault Categories
# -----------------------------------------------------------------------------
class FaultCategory(str, Enum):
    NORMAL = "NORMAL"
    FUEL_MIXTURE_DEGRADATION = "FUEL_MIXTURE_DEGRADATION"   # Carburetor / fuel-mixture delivery degradation
    FUEL_MIXTURE = "FUEL_MIXTURE"                             # Back-compat alias used by legacy tests and scripts
    OVERHEATING = "OVERHEATING"                               # Thermal / cooling degradation
    LUBRICATION_DEGRADATION = "LUBRICATION_DEGRADATION"     # Oil pressure / viscosity / lubrication degradation
    LUBRICATION = "LUBRICATION"                             # Back-compat alias used by legacy tests and scripts
    ABNORMAL_VIBRATION = "ABNORMAL_VIBRATION"                 # Mechanical imbalance / gearbox / mounting anomaly
    VIBRATION = "VIBRATION"                                   # Back-compat alias used by legacy tests and scripts
    SENSOR_ANOMALY = "SENSOR_ANOMALY"                         # Sensor bias / drift / failure


class EngineRegion(str, Enum):
    """Standardized affected-engine region identifiers for 3D engine visualisation and explainability."""
    FUEL_MIXTURE_REGION = "FUEL_MIXTURE_REGION"
    COMBUSTION_REGION = "COMBUSTION_REGION"
    CYLINDER_REGION = "CYLINDER_REGION"
    COOLING_REGION = "COOLING_REGION"
    LUBRICATION_REGION = "LUBRICATION_REGION"
    CRANKSHAFT_REGION = "CRANKSHAFT_REGION"
    BEARING_REGION = "BEARING_REGION"
    GEARBOX_REGION = "GEARBOX_REGION"
    ENGINE_MOUNT_REGION = "ENGINE_MOUNT_REGION"


FAULT_REGION_MAP: Dict[str, List[str]] = {
    FaultCategory.NORMAL.value: [EngineRegion.ENGINE_MOUNT_REGION.value],
    FaultCategory.FUEL_MIXTURE_DEGRADATION.value: [
        EngineRegion.FUEL_MIXTURE_REGION.value,
        EngineRegion.COMBUSTION_REGION.value,
    ],
    FaultCategory.OVERHEATING.value: [
        EngineRegion.CYLINDER_REGION.value,
        EngineRegion.COOLING_REGION.value,
    ],
    FaultCategory.LUBRICATION_DEGRADATION.value: [
        EngineRegion.LUBRICATION_REGION.value,
        EngineRegion.BEARING_REGION.value,
        EngineRegion.CRANKSHAFT_REGION.value,
    ],
    FaultCategory.ABNORMAL_VIBRATION.value: [
        EngineRegion.CRANKSHAFT_REGION.value,
        EngineRegion.BEARING_REGION.value,
        EngineRegion.GEARBOX_REGION.value,
        EngineRegion.ENGINE_MOUNT_REGION.value,
    ],
    FaultCategory.SENSOR_ANOMALY.value: [
        EngineRegion.CYLINDER_REGION.value,
        EngineRegion.ENGINE_MOUNT_REGION.value,
    ],
}


def canonical_fault_name(fault: FaultCategory | str) -> str:
    """Normalise short and long fault names to the canonical project taxonomy."""
    value = fault.value if isinstance(fault, FaultCategory) else str(fault)
    aliases = {
        "FUEL_MIXTURE": "FUEL_MIXTURE_DEGRADATION",
        "LUBRICATION": "LUBRICATION_DEGRADATION",
        "VIBRATION": "ABNORMAL_VIBRATION",
    }
    return aliases.get(value, value)


# -----------------------------------------------------------------------------
# Telemetry Parameters
# -----------------------------------------------------------------------------
PRIMARY_TELEMETRY_FIELDS: List[str] = [
    "timestamp",
    "rpm",
    "egt_c",
    "cht_c",
    "oil_pressure_bar",
    "oil_temperature_c",
    "fuel_flow_lph",
    "vibration_g",
    "altitude_ft",
    "ambient_temperature_c",
    "throttle",
    "engine_load",
    "power_kw",
]

EXPECTED_TELEMETRY_FIELDS: List[str] = [
    "expected_rpm",
    "expected_egt_c",
    "expected_cht_c",
    "expected_oil_pressure_bar",
    "expected_oil_temperature_c",
    "expected_fuel_flow_lph",
    "expected_vibration_g",
    "expected_power_kw",
]

RESIDUAL_FIELDS: List[str] = [
    "rpm_residual",
    "egt_residual",
    "cht_residual",
    "oil_pressure_residual",
    "oil_temperature_residual",
    "fuel_flow_residual",
    "vibration_residual",
]
