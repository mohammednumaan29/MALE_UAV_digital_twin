"""
Sensor Measurement Noise Model.
Simulates realistic transducer measurement uncertainty, electrical noise,
and quantization for aero-piston engine instrumentation.

Classification: [Measurement Uncertainty Model - Rule 1 Compliant]
Rule 1: Randomness may only represent sensor noise, small disturbances, and measurement uncertainty.
"""

import random
from typing import Dict, Any


class SensorNoiseModel:
    """
    Applies zero-mean Gaussian sensor noise with calibrated transducer standard deviations.
    Supports deterministic seeding for reproducible dataset generation (Phase 7).
    """

    # Calibrated standard deviations for engine transducers
    DEFAULT_NOISE_SIGMAS: Dict[str, float] = {
        "rpm": 4.0,                     # Optical / magnetic pickup noise (RPM)
        "egt_c": 1.2,                   # Type K thermocouple noise (°C)
        "cht_c": 0.35,                  # Resistance thermometer (Pt100/NTC) noise (°C)
        "oil_pressure_bar": 0.02,       # Piezoresistive pressure transducer noise (bar)
        "oil_temperature_c": 0.25,      # Oil temperature probe noise (°C)
        "fuel_flow_lph": 0.12,          # Turbine flowmeter pulse jitter (L/h)
        "vibration_g": 0.004,           # Accelerometer noise floor (g RMS)
        "altitude_ft": 1.5,             # Barometric altimeter noise (ft)
        "ambient_temperature_c": 0.15,  # Outside air temperature probe (°C)
        "throttle": 0.1,                # Throttle position sensor (TPS) noise (%)
        "engine_load": 0.002,           # Computed load noise
        "power_kw": 0.2,                # Estimated power noise (kW)
    }

    def __init__(self, seed: int | None = None, enabled: bool = True):
        """
        Initialize sensor noise model.

        Args:
            seed: Optional integer seed for reproducible random noise generation.
            enabled: If False, returns raw values without noise.
        """
        self.rng = random.Random(seed)
        self.enabled = enabled
        self.sigmas = dict(self.DEFAULT_NOISE_SIGMAS)

    def set_seed(self, seed: int | None) -> None:
        """Set random seed for reproducibility."""
        self.rng.seed(seed)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable noise injection."""
        self.enabled = enabled

    def apply_noise(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply sensor measurement noise to a telemetry dictionary.

        Args:
            telemetry: Raw deterministic telemetry state.

        Returns:
            Dict containing telemetry with realistic sensor noise applied.
        """
        if not self.enabled:
            return dict(telemetry)

        noisy = dict(telemetry)

        for key, sigma in self.sigmas.items():
            if key in noisy and isinstance(noisy[key], (int, float)):
                raw_val = float(noisy[key])
                noise = self.rng.gauss(0.0, sigma)
                val_with_noise = raw_val + noise

                # Guard against non-physical negative values
                if key in ["rpm", "fuel_flow_lph", "power_kw", "vibration_g", "engine_load", "altitude_ft"]:
                    val_with_noise = max(0.0, val_with_noise)
                elif key in ["oil_pressure_bar"]:
                    val_with_noise = max(0.5, val_with_noise)
                elif key in ["throttle"]:
                    val_with_noise = max(0.0, min(100.0, val_with_noise))

                # Proper sensor quantization
                if key == "rpm":
                    noisy[key] = round(val_with_noise)
                elif key in ["vibration_g"]:
                    noisy[key] = round(val_with_noise, 4)
                elif key in ["oil_pressure_bar"]:
                    noisy[key] = round(val_with_noise, 3)
                else:
                    noisy[key] = round(val_with_noise, 2)

        return noisy
