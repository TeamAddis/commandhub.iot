from fastapi import APIRouter, HTTPException

from models.schemas import AlarmSetRequest, AlarmStatusResponse, ErrorResponse
from mqtt.client import mqtt_bridge
from logger.transaction_log import transaction_log
import config

router = APIRouter(prefix="/alarms", tags=["alarms"])

_ALARM_STATUS_REQUEST_TOPIC = "bloom/mcu/alarm/status/request"
_ALARM_SET_TOPIC = "bloom/mcu/alarm/set"
_ALARM_STATUS_TOPIC = "bloom/mcu/alarm/status"


@router.get(
    "",
    response_model=AlarmStatusResponse,
    responses={408: {"model": ErrorResponse}},
    summary="Get alarm configuration",
    operation_id="getAlarms",
)
def get_alarms():
    entry = transaction_log.start_transaction("GET", "/alarms")
    response = mqtt_bridge.publish_and_wait(
        _ALARM_STATUS_REQUEST_TOPIC,
        _ALARM_STATUS_TOPIC,
        {"message": "status"},
        config.MQTT_RESPONSE_TIMEOUT,
        log_entry=entry,
    )
    if response is None:
        transaction_log.finish_transaction(entry, 408, timed_out=True)
        raise HTTPException(status_code=408, detail="Device did not respond within timeout period")
    transaction_log.finish_transaction(entry, 200)
    return AlarmStatusResponse(**response)


@router.put(
    "",
    response_model=AlarmStatusResponse,
    responses={408: {"model": ErrorResponse}},
    summary="Set alarm configuration",
    operation_id="setAlarms",
)
def set_alarms(request: AlarmSetRequest):
    entry = transaction_log.start_transaction("PUT", "/alarms")
    payload = {"alarms": [alarm.model_dump() for alarm in request.alarms]}
    response = mqtt_bridge.publish_and_wait(
        _ALARM_SET_TOPIC,
        _ALARM_STATUS_TOPIC,
        payload,
        config.MQTT_RESPONSE_TIMEOUT,
        log_entry=entry,
    )
    if response is None:
        transaction_log.finish_transaction(entry, 408, timed_out=True)
        raise HTTPException(status_code=408, detail="Device did not respond within timeout period")
    transaction_log.finish_transaction(entry, 200)
    return AlarmStatusResponse(**response)
