from decouple import config

MQTT_BROKER_HOST = config("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = config("MQTT_BROKER_PORT", default=1883, cast=int)
MQTT_USERNAME = config("MQTT_USERNAME")
MQTT_PASSWORD = config("MQTT_PASSWORD")
API_KEY = config("API_KEY")
MQTT_RESPONSE_TIMEOUT = config("MQTT_RESPONSE_TIMEOUT", default=5, cast=int)

# Credentials for the /logs Basic Auth browser UI
LOGS_USER = config("LOGS_USER", default="")
LOGS_PASSWORD = config("LOGS_PASSWORD", default="")
