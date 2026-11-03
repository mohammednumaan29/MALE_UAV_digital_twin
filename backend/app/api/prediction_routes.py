"""
Digital Twin Prediction API Endpoints.
Phase 1: Deterministic Physics-Informed Expected State API.
"""

from fastapi import APIRouter, status
from app.schemas.prediction import DigitalTwinPredictRequest, DigitalTwinPredictResponse
from app.services.digital_twin_service import digital_twin_service

router = APIRouter(prefix="/digital-twin", tags=["Digital Twin"])


@router.post(
    "/predict",
    response_model=DigitalTwinPredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Expected Engine State (Physics-Informed)",
    description=(
        "Compute deterministic, physics-informed expected engine state based on "
        "flight operating conditions (throttle, altitude, ambient temperature). "
        "Does NOT use machine learning."
    )
)
async def predict_engine_state(
    request: DigitalTwinPredictRequest
) -> DigitalTwinPredictResponse:
    """Evaluate physics model equations and return expected engine parameters."""
    return digital_twin_service.predict_expected_state(request)
