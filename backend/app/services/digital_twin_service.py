"""
Digital Twin Service Layer.
Orchestrates virtual physics twin prediction requests and delegates to physics models.
"""

from typing import Dict, Any
from app.physics.engine_model import physics_engine
from app.schemas.prediction import DigitalTwinPredictRequest, DigitalTwinPredictResponse
from app.utils.logging import logger


class DigitalTwinService:
    """Service orchestrating physics-based digital twin queries."""

    def __init__(self):
        self.engine = physics_engine

    def predict_expected_state(
        self,
        request: DigitalTwinPredictRequest
    ) -> DigitalTwinPredictResponse:
        """
        Evaluate physics equations for the given operating conditions.
        """
        logger.debug(
            "Evaluating physics twin: throttle=%.1f%%, alt=%.0fft, Tamb=%.1fC",
            request.throttle,
            request.altitude_ft,
            request.ambient_temperature_c
        )

        state: Dict[str, Any] = self.engine.predict_state(
            throttle=request.throttle,
            altitude_ft=request.altitude_ft,
            ambient_temperature_c=request.ambient_temperature_c,
            rpm_override=request.rpm_override
        )

        return DigitalTwinPredictResponse(**state)


digital_twin_service = DigitalTwinService()
