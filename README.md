# commandhub.iot

Local IoT gateway REST API. Bridges an iOS app (or any HTTP client) to IoT devices via a local Mosquitto MQTT broker running on a Raspberry Pi. Built with FastAPI + paho-mqtt. Designed to be generic and expandable beyond the initial Bloom plant watering use case.

---

## Architecture

```
iOS App → HTTPS → Cloudflare Tunnel → Raspberry Pi REST API → MQTT → IoT Device
```

The MQTT broker stays completely internal and is never directly exposed to the internet. Only the REST API is the public-facing surface, secured by API key auth and HTTPS via Cloudflare.

---

## Prerequisites

- Raspberry Pi (any model running Raspberry Pi OS)
- Python 3.10 or higher
- Mosquitto MQTT broker installed and running locally on the Pi
  > **Note:** Setup of Mosquitto is out of scope for this repo. Refer to the [official Mosquitto documentation](https://mosquitto.org/documentation/) for installation instructions.
- A Cloudflare Tunnel (optional — required for off-network access from iOS)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/TeamAddis/commandhub.iot
cd commandhub.iot
```

### 2. Configure environment variables

See [Configuration & Credentials](#configuration--credentials-python-decouple) below for full details.

```bash
cp .env.example .env
nano .env   # fill in your values before continuing
```

### 3. Run the setup script

```bash
chmod +x setup.sh
sudo ./setup.sh
```

The script will install system dependencies, create a Python virtual environment, install Python packages, register the systemd service, and start it automatically.

### 4. Confirm the service is running

```bash
sudo systemctl status commandhub
```

---

## Configuration & Credentials (python-decouple)

### How python-decouple works

- `python-decouple` loads configuration from a `.env` file in the project root, or from real environment variables set on the system.
- It never silently falls back to default values for required secrets — if a required variable is missing, the app will fail to start with a clear error.
- The `.env` file is listed in `.gitignore` and should **never be committed to version control**.

### Setup steps

```bash
cp .env.example .env
nano .env   # or use any editor
```

### Variable reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `MQTT_BROKER_HOST` | ✅ | — | IP address of the local Mosquitto broker (e.g. `192.168.1.x`) |
| `MQTT_BROKER_PORT` | ✅ | `1883` | Mosquitto port (`1883` = plain, `8883` = TLS) |
| `MQTT_USERNAME` | ✅ | — | Mosquitto username |
| `MQTT_PASSWORD` | ✅ | — | Mosquitto password |
| `API_KEY` | ✅ | — | Secret key for `X-API-Key` header auth |
| `MQTT_RESPONSE_TIMEOUT` | ❌ | `5` | Seconds to wait for device response before returning `408` |

### Generating a strong API key

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

This generates a cryptographically secure 64-character hex string. Copy the output into the `.env` file as the value for `API_KEY`. Use the same value in your iOS app as the `X-API-Key` request header.

### Best practices

> **Security reminders:**
> - Never hardcode credentials in source files
> - Never commit `.env` to git (it is already in `.gitignore`)
> - Rotate `API_KEY` immediately if you believe it has been exposed
> - Use a strong, unique password for your Mosquitto user
> - Restrict `.env` file permissions on the Pi:
>   ```bash
>   chmod 600 .env
>   ```

---

## Managing the Service

```bash
sudo systemctl start commandhub      # start
sudo systemctl stop commandhub       # stop
sudo systemctl restart commandhub    # restart after config changes
sudo systemctl status commandhub     # check running status
journalctl -u commandhub -f          # tail live logs
```

---

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- All endpoints require the `X-API-Key` header
- Full OpenAPI 3.0.3 spec is available in [`openapi.yaml`](openapi.yaml)

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/pump` | Turn pump on or off |
| `GET` | `/pump/status` | Get current pump status |
| `PUT` | `/pump/runtime` | Set max pump runtime (ms) |
| `GET` | `/alarms` | Get alarm schedule |
| `PUT` | `/alarms` | Update alarm schedule |
| `GET` | `/mcu/status` | Get device firmware version |

---

## Remote Access (Cloudflare Tunnel)

Cloudflare Tunnel exposes the local API to the internet over HTTPS without port forwarding or VPN configuration.

- Once configured, the iOS app hits `https://your-tunnel-url.com` instead of the local IP
- No VPN or special iPhone network configuration required
- The MQTT broker remains internal and is never exposed

Refer to the [Cloudflare Tunnel documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) for setup instructions.

---

## Project Structure

```
commandhub.iot/
├── main.py                  # FastAPI app, auth dependency, lifespan
├── config.py                # Environment variable loading via python-decouple
├── routers/
│   ├── pump.py              # /pump endpoints
│   ├── alarms.py            # /alarms endpoints
│   └── mcu.py               # /mcu endpoints
├── mqtt/
│   └── client.py            # MQTTBridge: paho-mqtt pub/sub bridge
├── models/
│   └── schemas.py           # Pydantic request/response models
├── openapi.yaml             # OpenAPI 3.0.3 spec
├── setup.sh                 # One-shot Pi installer
├── commandhub.service       # systemd unit file
├── requirements.txt
├── .env.example             # Environment variable template
└── README.md
```

