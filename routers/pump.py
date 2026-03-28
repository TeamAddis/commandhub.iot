from fastapi import APIRouter, HTTPException

from models.schemas import (
    PumpControlRequest,
    PumpStatusResponse,
    PumpRuntimeRequest,
    ErrorResponse,
)
from mqtt.client import mqtt_bridge
import config

router = APIRouter(prefix="/pump", tags=["pump"])

_PUMP_CONTROL_TOPIC = "bloom/mcu/pump/control"
_PUMP_STATUS_REQUEST_TOPIC = "bloom/mcu/pump/status/request"
_PUMP_STATUS_TOPIC = "bloom/mcu/pump/status"
_PUMP_RUNTIME_SET_TOPIC = "bloom/mcu/pump/runtime/set"


@router.post(
    "",
    response_model=PumpStatusResponse,
    responses={408: {"model": ErrorResponse}},
    summary="Control the pump",
    operation_id="controlPump",
)
def control_pump(request: PumpControlRequest):
    payload = {"message": request.state}
    response = mqtt_bridge.publish_and_wait(
        _PUMP_CONTROL_TOPIC,
        _PUMP_STATUS_TOPIC,
        payload,
        config.MQTT_RESPONSE_TIMEOUT,
    )
    if response is None:
        raise HTTPException(status_code=408, detail="Device did not respond within timeout period")
    return PumpStatusResponse(**response)


@router.get(
    "/status",
    response_model=PumpStatusResponse,
    responses={408: {"model": ErrorResponse}},
    summary="Get pump status",
    operation_id="getPumpStatus",
)
def get_pump_status():
    response = mqtt_bridge.publish_and_wait(
        _PUMP_STATUS_REQUEST_TOPIC,
        _PUMP_STATUS_TOPIC,
        {"message": "status"},
        config.MQTT_RESPONSE_TIMEOUT,
    )
    if response is None:
        raise HTTPException(status_code=408, detail="Device did not respond within timeout period")
    return PumpStatusResponse(**response)


@router.put(
    "/runtime",
    response_model=None,
    status_code=200,
    summary="Set maximum pump runtime",
    operation_id="setPumpRuntime",
    responses={400: {"model": ErrorResponse}},
)
def set_pump_runtime(request: PumpRuntimeRequest):
    mqtt_bridge.publish(_PUMP_RUNTIME_SET_TOPIC, {"maxPumpRuntime": request.maxPumpRuntime})

