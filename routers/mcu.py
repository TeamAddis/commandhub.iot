from fastapi import APIRouter, HTTPException

from models.schemas import McuStatusResponse, ErrorResponse
from mqtt.client import mqtt_bridge
from logger.transaction_log import transaction_log
import config

router = APIRouter(prefix="/mcu", tags=["mcu"])

_MCU_STATUS_REQUEST_TOPIC = "bloom/mcu/status/request"
_MCU_STATUS_TOPIC = "bloom/mcu/status"


@router.get(
    "/status",
    response_model=McuStatusResponse,
    responses={408: {"model": ErrorResponse}},
    summary="Get MCU status",
    operation_id="getMcuStatus",
)
def get_mcu_status():
    entry = transaction_log.start_transaction("GET", "/mcu/status")
    response = mqtt_bridge.publish_and_wait(
        _MCU_STATUS_REQUEST_TOPIC,
        _MCU_STATUS_TOPIC,
        {"message": "status"},
        config.MQTT_RESPONSE_TIMEOUT,
        log_entry=entry,
    )
    if response is None:
        transaction_log.finish_transaction(entry, 408, timed_out=True)
        raise HTTPException(status_code=408, detail="Device did not respond within timeout period")
    transaction_log.finish_transaction(entry, 200)
    return McuStatusResponse(**response)
