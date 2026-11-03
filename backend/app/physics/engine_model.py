"""
Rotax 914 Virtual Engine Physics Model.
Top-level physics-informed orchestrator integrating atmosphere, turbocharger, airflow,
power, combustion, thermal, lubrication, and mechanical dynamics.

Classification: [Physics-Informed Integrated Virtual Engine]
Reference: Rotax 914 F Maintenance & Operators Manuals, Aircraft Engine Thermodynamic Principles.
"""

from typing import Dict, Any
from app.physics.atmosphere import compute_atmospheric_state
from app.physics.turbocharger import compute_manifold_state
from app.physics.airflow import compute_airflow_state
from app.physics.power import compute_expected_rpm, compute_power_and_torque
from app.physics.combustion import compute_fuel_flow
from app.physics.thermal import compute_thermal_state
from app.physics.lubrication import compute_oil_pressure
from app.physics.mechanical import compute_baseline_vibration


class Rotax914PhysicsModel:
    """
    Virtual Engine Physics Twin for the Rotax 914 Turbocharged Aero-Piston Engine.
    Purely deterministic mathematical equations, thermodynamics, and engineering correlations.
    Does NOT depend on Machine Learning.
    """

    def __init__(self):
        self.model_name = "Rotax 914-F Physics-Informed Digital Twin"
        self.version = "1.0.0"

    def predict_state(
        self,
        throttle: float,
        altitude_ft: float,
        ambient_temperature_c: float,
        rpm_override: float | None = None,
    ) -> Dict[str, Any]:
        """
        Predict full expected engine operational state from boundary/flight conditions.

        Args:
            throttle: Throttle lever angle setting (0.0% to 100.0%).
            altitude_ft: Flight altitude in feet (0 to 30,000 ft).
            ambient_temperature_c: Outside ambient air temperature (°C).
            rpm_override: Optional forced RPM (for observer/residual comparison mode).

        Returns:
            Dict containing complete expected engine state.
        """
        # 1. Boundary Condition Validation and Clamping
        th_val = max(0.0, min(100.0, float(throttle)))
        alt_val = max(0.0, float(altitude_ft))
        t_amb_val = float(ambient_temperature_c)

        # 2. Atmospheric Layer (Pressure, Temperature, Density)
        # [Standard Physical Equation: ISA]
        atmo = compute_atmospheric_state(
            altitude_ft=alt_val,
            ambient_temperature_c=t_amb_val
        )

        # 3. Engine Rotational Speed (RPM)
        # If rpm_override is provided, use it; otherwise compute equilibrium RPM from throttle
        if rpm_override is not None:
            expected_rpm = max(1000.0, min(6200.0, float(rpm_override)))
        else:
            expected_rpm = compute_expected_rpm(th_val)

        # 4. Turbocharger & Intake Manifold State (MAP, Manifold Temp, Boost)
        # [Manufacturer Specification & Thermodynamic Compression]
        manifold = compute_manifold_state(
            throttle_pct=th_val,
            ambient_pressure_bar=atmo["pressure_bar"],
            ambient_temperature_k=atmo["temperature_k"],
            altitude_ft=alt_val,
            rpm=expected_rpm
        )

        # 5. Airflow Dynamics (Volumetric Efficiency, Air Mass Flow)
        # [Standard Physical Equation: Four-Stroke Air Induction]
        airflow = compute_airflow_state(
            rpm=expected_rpm,
            manifold_pressure_bar=manifold["manifold_pressure_bar"],
            manifold_temperature_k=manifold["manifold_temperature_k"]
        )

        # 6. Mechanical Power & Torque Output
        # [Standard Physical Equation: P = T * omega]
        power_state = compute_power_and_torque(
            rpm=expected_rpm,
            throttle_pct=th_val,
            manifold_pressure_bar=manifold["manifold_pressure_bar"],
            air_density_kgm3=atmo["density_kgm3"]
        )

        # 7. Fuel Consumption & Energy Balance
        # [Standard Physical Equation: P = m_dot_f * LHV * eta]
        combustion = compute_fuel_flow(
            power_kw=power_state["power_kw"],
            engine_load=power_state["engine_load"],
            air_mass_flow_kg_s=airflow["air_mass_flow_kg_s"]
        )

        # 8. Thermal Heat Balance (EGT, CHT, Oil Temperature)
        # [Engineering Correlation & Liquid-Cooling Balance]
        thermal = compute_thermal_state(
            engine_load=power_state["engine_load"],
            rpm=expected_rpm,
            ambient_temperature_c=t_amb_val,
            altitude_ft=alt_val,
            fuel_flow_lph=combustion["fuel_flow_lph"]
        )

        # 9. Lubrication Dynamics (Oil Pressure & Viscosity)
        # [Hydrodynamic Pump Flow & Temperature Viscosity Decay]
        lubrication = compute_oil_pressure(
            rpm=expected_rpm,
            oil_temperature_c=thermal["expected_oil_temperature_c"]
        )

        # 10. Mechanical Vibration (Rotational Unbalance & Combustion Harmonics)
        # [Harmonic Excitation Model]
        vibration = compute_baseline_vibration(
            rpm=expected_rpm,
            engine_load=power_state["engine_load"]
        )

        # Consolidated Result
        return {
            # Core primary expected variables required by specification
            "expected_rpm": round(expected_rpm, 1),
            "expected_egt_c": round(thermal["expected_egt_c"], 1),
            "expected_cht_c": round(thermal["expected_cht_c"], 1),
            "expected_oil_pressure_bar": round(lubrication["expected_oil_pressure_bar"], 2),
            "expected_oil_temperature_c": round(thermal["expected_oil_temperature_c"], 1),
            "expected_fuel_flow_lph": round(combustion["fuel_flow_lph"], 1),
            "expected_vibration_g": round(vibration["expected_vibration_g"], 3),
            "expected_power_kw": round(power_state["power_kw"], 1),
            "expected_torque_nm": round(power_state["torque_nm"], 1),

            # Intermediate physics parameters
            "engine_load": round(power_state["engine_load"], 3),
            "manifold_pressure_bar": round(manifold["manifold_pressure_bar"], 3),
            "manifold_pressure_inhg": round(manifold["manifold_pressure_inhg"], 1),
            "ambient_pressure_bar": round(atmo["pressure_bar"], 3),
            "air_density_kgm3": round(atmo["density_kgm3"], 3),
            "air_mass_flow_kg_h": round(airflow["air_mass_flow_kg_h"], 1),
            "volumetric_efficiency": round(airflow["volumetric_efficiency"], 3),
            "air_fuel_ratio": round(combustion["air_fuel_ratio"], 2),
            "throttle": th_val,
            "altitude_ft": alt_val,
            "ambient_temperature_c": t_amb_val,
        }


# Global singleton instance for service calls
physics_engine = Rotax914PhysicsModel()
