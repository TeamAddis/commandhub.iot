# commandhub.iot

A Python FastAPI project that acts as a REST API gateway bridging an iOS app and a local
Mosquitto MQTT broker running on a Raspberry Pi. The API translates HTTP requests into MQTT
publish/subscribe interactions with an IoT device (Arduino MKR WiFi 1010 running the Bloom
plant watering firmware).

The API is designed to be generic enough to support future IoT projects beyond the initial
Bloom plant watering use case.

---

## Prerequisites

- Python 3.10+
- A running [Mosquitto](https://mosquitto.org/) MQTT broker (e.g., on a Raspberry Pi)
- Arduino MKR WiFi 1010 flashed with the Bloom firmware, pointing at the same broker

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/TeamAddis/commandhub.iot.git
cd commandhub.iot
```

### 2. Create your environment file

```bash
cp .env.example .env
```

Edit `.env` and fill in your MQTT broker host/credentials and a secret API key.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## API Documentation

Once the server is running, open the auto-generated Swagger UI in your browser:

```
http://localhost:8000/docs
```

The full OpenAPI 3.0.3 specification is also available in [`openapi.yaml`](openapi.yaml).

All endpoints require the `X-API-Key` header to be set to the value configured in `.env`.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/pump` | Turn the pump on or off |
| `GET` | `/pump/status` | Get the current pump status |
| `PUT` | `/pump/runtime` | Set the maximum pump runtime (ms) |
| `GET` | `/alarms` | Get the current alarm schedule |
| `PUT` | `/alarms` | Update the alarm schedule |
| `GET` | `/mcu/status` | Get firmware version from the MCU |

---

## Remote Access via Cloudflare Tunnel

To securely expose the API over the internet without opening router ports, use a
[Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/):

```bash
cloudflared tunnel --url http://localhost:8000
```

The MQTT broker stays completely internal — it is never exposed to the internet.
Only the REST API is the public-facing surface, secured by the API key and HTTPS via Cloudflare.

