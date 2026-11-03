"""
Atmospheric Physics Model (ISA - International Standard Atmosphere).
Computes pressure, temperature, and air density as a function of altitude and ambient temperature.

Classification: [Standard Physical Equation]
Reference: ICAO Standard Atmosphere (Doc 7488/3), Ideal Gas Law.
"""

import math
from typing import Dict

# -----------------------------------------------------------------------------
# ISA Physical Constants
# -----------------------------------------------------------------------------
# [Standard Physical Equation Constants]
P0_SEA_LEVEL_PA: float = 101325.0      # Standard sea-level pressure (Pa)
T0_SEA_LEVEL_K: float = 288.15         # Standard sea-level temperature (15.0 °C, K)
RHO0_SEA_LEVEL_KGM3: float = 1.225     # Standard sea-level air density (kg/m³)
LAPSE_RATE_K_PER_M: float = 0.0065     # Troposphere lapse rate (K/m)
GRAVITY_M_PER_S2: float = 9.80665      # Gravitational acceleration (m/s²)
GAS_CONSTANT_AIR: float = 287.05287    # Specific gas constant for dry air (J/(kg·K))
FEET_TO_METERS: float = 0.3048         # Conversion factor: 1 ft = 0.3048 m
EXPONENT_ISA: float = GRAVITY_M_PER_S2 / (GAS_CONSTANT_AIR * LAPSE_RATE_K_PER_M)  # ~5.2559


def compute_atmospheric_state(
    altitude_ft: float,
    ambient_temperature_c: float | None = None
) -> Dict[str, float]:
    """
    Calculate atmospheric pressure, temperature, and density.

    Args:
        altitude_ft: Geometric altitude in feet (0 to 36,000 ft troposphere range).
        ambient_temperature_c: Optional ambient air temperature (°C).
                               If None, standard ISA temperature at altitude is used.

    Returns:
        Dict containing:
            - altitude_m: Altitude in meters
            - pressure_pa: Ambient static pressure (Pa)
            - pressure_bar: Ambient static pressure (bar)
            - temperature_k: Ambient temperature (K)
            - temperature_c: Ambient temperature (°C)
            - density_kgm3: Air density (kg/m³)
            - density_ratio_sigma: Density relative to sea level (rho / rho0)
            - pressure_ratio_delta: Pressure relative to sea level (P / P0)
    """
    # Guard against invalid negative altitude if encountered
    alt_ft = max(0.0, float(altitude_ft))
    alt_m = alt_ft * FEET_TO_METERS

    # ISA standard temperature at altitude (K)
    # [Standard Physical Equation]
    t_isa_k = T0_SEA_LEVEL_K - LAPSE_RATE_K_PER_M * alt_m
    t_isa_k = max(t_isa_k, 216.65)  # Tropopause lower limit at 11,000 m

    # ISA barometric pressure equation for the troposphere
    # P = P0 * (1 - L*h / T0) ^ (g / (R*L))
    # [Standard Physical Equation]
    temp_ratio = 1.0 - (LAPSE_RATE_K_PER_M * alt_m / T0_SEA_LEVEL_K)
    temp_ratio = max(0.01, temp_ratio)
    pressure_pa = P0_SEA_LEVEL_PA * math.pow(temp_ratio, EXPONENT_ISA)
    pressure_bar = pressure_pa / 100000.0

    # Actual temperature: user specified or standard ISA
    if ambient_temperature_c is not None:
        t_actual_c = float(ambient_temperature_c)
        t_actual_k = t_actual_c + 273.15
    else:
        t_actual_k = t_isa_k
        t_actual_c = t_actual_k - 273.15

    # Ideal Gas Law for air density: rho = P / (R * T)
    # [Standard Physical Equation]
    t_actual_k = max(180.0, t_actual_k)  # Physical sanity clamp
    density_kgm3 = pressure_pa / (GAS_CONSTANT_AIR * t_actual_k)

    # Relative ratios
    density_ratio_sigma = density_kgm3 / RHO0_SEA_LEVEL_KGM3
    pressure_ratio_delta = pressure_pa / P0_SEA_LEVEL_PA

    return {
        "altitude_m": alt_m,
        "pressure_pa": pressure_pa,
        "pressure_bar": pressure_bar,
        "temperature_k": t_actual_k,
        "temperature_c": t_actual_c,
        "density_kgm3": density_kgm3,
        "density_ratio_sigma": density_ratio_sigma,
        "pressure_ratio_delta": pressure_ratio_delta,
    }
