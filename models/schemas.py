from pydantic import BaseModel, Field
from typing import List, Literal


class PumpControlRequest(BaseModel):
    state: Literal["on", "off"]


class PumpStatusResponse(BaseModel):
    status: Literal["on", "off"]


class PumpRuntimeRequest(BaseModel):
    maxPumpRuntime: int = Field(
        ..., ge=1, le=60000, description="Max pump runtime in milliseconds"
    )


class Alarm(BaseModel):
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(..., ge=0, le=59)
    enabled: bool
    valid: bool


class AlarmSetRequest(BaseModel):
    alarms: List[Alarm] = Field(..., min_length=1, max_length=4)


class AlarmStatusResponse(BaseModel):
    alarms: List[Alarm]


class McuStatusResponse(BaseModel):
    version: int


class ErrorResponse(BaseModel):
    detail: str
