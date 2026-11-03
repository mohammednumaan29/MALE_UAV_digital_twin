"""
Combustion and Fuel Flow Physics Model.
Implements the fuel energy balance P = m_dot_f * LHV * eta and carburetor AFR cross-check.

Classification: [Standard Physical Equation & Engineering Correlation]
Formulas:
    P = m_dot_f * LHV * eta_thermal
    m_dot_f = P / (LHV * eta_thermal)
    Fuel Flow (LPH) = (m_dot_f * 3600) / rho_fuel
"""

from typing import Dict

# -----------------------------------------------------------------------------
# Combustion & Thermochemical Parameters
# -----------------------------------------------------------------------------
# [Standard Physical Equation Constants]
LHV_FUEL_J_PER_KG: float = 43.5e6        # Lower heating value of avgas / mogas (43.5 MJ/kg)
RHO_FUEL_KG_PER_L: float = 0.720         # Aviation gasoline / motor gasoline density (kg/L)

# [Engineering Assumption]
THERMAL_EFFICIENCY_BASE: float = 0.34    # Nominal brake thermal efficiency (34%)
AFR_STOICHIOMETRIC: float = 14.7         # Stoichiometric air-fuel ratio
AFR_TAKEOFF_RICH: float = 12.2           # Full-power takeoff enriched mixture (cooling)
AFR_CRUISE: float = 14.0                 # Cruise economy mixture


def compute_air_fuel_ratio(engine_load: float) -> float:
    """
    Compute effective carburetor air-fuel ratio based on carburetor metering jet behavior.
    Under high throttle / turbo boost, the carburetor enriches mixture to prevent detonation.

    Classification: [Engineering Correlation: Carburetor Enrichment Schedule]
    """
    load = max(0.0, min(1.0, float(engine_load)))
    # At low/idle load: ~13.5 (slightly rich idle)
    # At cruise (0.4 to 0.75): ~14.2 - 14.5
    # Above 0.75: Progressive power enrichment circuit down to 12.2
    if load < 0.3:
        return 13.5 + (load / 0.3) * 0.7
    elif load <= 0.75:
        return 14.2 - ((load - 0.3) / 0.45) * 0.4
    else:
        # High power enrichment
        enrichment_factor = (load - 0.75) / 0.25
        return 13.8 - enrichment_factor * (13.8 - AFR_TAKEOFF_RICH)


def compute_fuel_flow(
    power_kw: float,
    engine_load: float,
    air_mass_flow_kg_s: float | None = None
) -> Dict[str, float]:
    """
    Calculate fuel mass flow rate and volumetric fuel flow in liters/hour.

    Classification: [Standard Physical Equation & Engineering Balance]
    Formula:
        m_dot_f = P_watts / (LHV * eta_thermal)

    Args:
        power_kw: Engine brake power in kW.
        engine_load: Normalized engine load fraction (0.0 to 1.0).
        air_mass_flow_kg_s: Optional airflow rate for dual-verification against AFR.

    Returns:
        Dict containing:
            - fuel_flow_lph: Volumetric fuel flow rate (L/h)
            - fuel_flow_kg_s: Mass fuel flow rate (kg/s)
            - fuel_flow_kg_h: Mass fuel flow rate (kg/h)
            - thermal_efficiency: Brake thermal efficiency (eta_thermal)
            - air_fuel_ratio: Air-to-fuel ratio (AFR)
            - bsfc_g_kwh: Brake specific fuel consumption (g/(kW·h))
    """
    power_watts = max(1500.0, float(power_kw) * 1000.0)
    load = max(0.08, min(1.0, float(engine_load)))

    # Thermal efficiency varies with engine load (lower at idle/part throttle due to throttling losses)
    # [Engineering Correlation]
    eta_thermal = THERMAL_EFFICIENCY_BASE * (0.65 + 0.35 * (load ** 0.6))
    eta_thermal = max(0.18, min(0.34, eta_thermal))

    # Energy balance primary calculation
    # P = m_dot_f * LHV * eta  ==>  m_dot_f = P / (LHV * eta)
    # [Standard Physical Equation]
    fuel_flow_kg_s = power_watts / (LHV_FUEL_J_PER_KG * eta_thermal)

    # Cross-check against air-fuel ratio
    afr = compute_air_fuel_ratio(load)
    if air_mass_flow_kg_s is not None and air_mass_flow_kg_s > 0.001:
        # m_dot_f_afr = m_dot_air / AFR
        m_dot_f_afr = air_mass_flow_kg_s / afr
        # Harmonize energy balance and airflow metering with 85% energy balance weight
        fuel_flow_kg_s = 0.85 * fuel_flow_kg_s + 0.15 * m_dot_f_afr

    fuel_flow_kg_h = fuel_flow_kg_s * 3600.0

    # Volumetric fuel flow in L/h
    # [Standard Physical Equation]
    fuel_flow_lph = fuel_flow_kg_h / RHO_FUEL_KG_PER_L

    # Brake specific fuel consumption (BSFC) in g/(kW·h)
    bsfc_g_kwh = (fuel_flow_kg_h * 1000.0) / (power_kw if power_kw > 0.1 else 1.0)

    return {
        "fuel_flow_lph": fuel_flow_lph,
        "fuel_flow_kg_s": fuel_flow_kg_s,
        "fuel_flow_kg_h": fuel_flow_kg_h,
        "thermal_efficiency": eta_thermal,
        "air_fuel_ratio": afr,
        "bsfc_g_kwh": bsfc_g_kwh,
    }
