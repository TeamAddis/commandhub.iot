import json
import threading
import time
import logging

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

import config
from logger.transaction_log import transaction_log

logger = logging.getLogger(__name__)


class MQTTBridge:
    def __init__(self):
        self._client = mqtt.Client(CallbackAPIVersion.VERSION1)
        self._client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        self._response_event = threading.Event()
        self._response_payload: dict | None = None
        self._response_topic: str | None = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self):
        self._client.connect(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT)
        self._client.loop_start()
        self._client.subscribe("bloom/#")

    def disconnect(self):
        self._client.loop_stop()
        self._client.disconnect()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT connected to %s:%s", config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT)
        else:
            logger.error("MQTT connection failed with code %s", rc)

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning("MQTT unexpectedly disconnected (rc=%s). Will attempt reconnect.", rc)
            self._reconnect()

    def _on_message(self, client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
        except json.JSONDecodeError:
            payload = message.payload.decode()

        transaction_log.add_mqtt_event(message.topic, payload)

        with self._lock:
            if self._response_topic and message.topic == self._response_topic:
                self._response_payload = payload if isinstance(payload, dict) else None
                self._response_event.set()

    # ------------------------------------------------------------------
    # Reconnection
    # ------------------------------------------------------------------

    def _reconnect(self):
        while True:
            try:
                logger.info("Attempting MQTT reconnect...")
                self._client.reconnect()
                logger.info("MQTT reconnected successfully.")
                break
            except Exception as exc:
                logger.warning("Reconnect failed: %s. Retrying in 5s.", exc)
                time.sleep(5)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def publish(self, topic: str, payload: dict, log_entry=None):
        if log_entry:
            transaction_log.add_mqtt_step(log_entry, "publish", topic, payload)
        self._client.publish(topic, json.dumps(payload))

    def publish_and_wait(
        self,
        command_topic: str,
        response_topic: str,
        payload: dict,
        timeout: int | None = None,
        log_entry=None,
    ) -> dict | None:
        if timeout is None:
            timeout = config.MQTT_RESPONSE_TIMEOUT

        with self._lock:
            self._response_topic = response_topic
            self._response_payload = None
            self._response_event.clear()

        self._client.subscribe(response_topic)
        if log_entry:
            transaction_log.add_mqtt_step(log_entry, "publish", command_topic, payload)
        self._client.publish(command_topic, json.dumps(payload))

        received = self._response_event.wait(timeout=timeout)

        self._client.unsubscribe(response_topic)

        with self._lock:
            self._response_topic = None
            result = self._response_payload

        if not received:
            logger.warning("Timeout waiting for response on %s", response_topic)
            return None

        if log_entry and result:
            transaction_log.add_mqtt_step(log_entry, "receive", response_topic, result)

        return result


mqtt_bridge = MQTTBridge()
