import threading
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MqttEvent:
    timestamp: datetime
    direction: str
    topic: str
    payload: dict | str


@dataclass
class TransactionStep:
    direction: str
    topic: str
    payload: dict


@dataclass
class TransactionEntry:
    id: str
    timestamp: datetime
    method: str
    path: str
    steps: list[TransactionStep] = field(default_factory=list)
    status_code: int | None = None
    duration_ms: int | None = None
    timed_out: bool = False


class TransactionLog:
    def __init__(self, maxlen=100):
        self._transactions: deque[TransactionEntry] = deque(maxlen=maxlen)
        self._mqtt_events: deque[MqttEvent] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def start_transaction(self, method: str, path: str) -> TransactionEntry:
        entry = TransactionEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            method=method,
            path=path,
        )
        with self._lock:
            self._transactions.append(entry)
        return entry

    def finish_transaction(
        self, entry: TransactionEntry, status_code: int, timed_out: bool = False
    ):
        elapsed = datetime.now() - entry.timestamp
        entry.status_code = status_code
        entry.duration_ms = int(elapsed.total_seconds() * 1000)
        entry.timed_out = timed_out

    def add_mqtt_step(
        self, entry: TransactionEntry, direction: str, topic: str, payload: dict
    ):
        step = TransactionStep(direction=direction, topic=topic, payload=payload)
        with self._lock:
            entry.steps.append(step)

    def add_mqtt_event(self, topic: str, payload: dict | str):
        event = MqttEvent(
            timestamp=datetime.now(),
            direction="received",
            topic=topic,
            payload=payload,
        )
        with self._lock:
            self._mqtt_events.append(event)

    def get_transactions(self) -> list[TransactionEntry]:
        with self._lock:
            return list(reversed(list(self._transactions)))

    def get_mqtt_events(self) -> list[MqttEvent]:
        with self._lock:
            return list(reversed(list(self._mqtt_events)))


transaction_log = TransactionLog()
