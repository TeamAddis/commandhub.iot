from contextlib import asynccontextmanager

from fastapi import FastAPI, Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

import config
from mqtt.client import mqtt_bridge
from routers import pump, alarms, mcu

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != config.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt_bridge.connect()
    yield
    mqtt_bridge.disconnect()


app = FastAPI(
    title="commandhub.iot",
    description="Local IoT gateway API",
    version="1.0.0",
    lifespan=lifespan,
    dependencies=[Security(verify_api_key)],
)

app.include_router(pump.router)
app.include_router(alarms.router)
app.include_router(mcu.router)
