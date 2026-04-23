"""UDP paket dinleyici — F1 25 telemetri soketini thread ile dinler.

Planlama: .planning/02-architecture.md#udp_listenerpy, .planning/05-phases.md Faz 1
"""
from __future__ import annotations

import logging
import socket
import threading
from dataclasses import dataclass
from queue import Empty, Full, Queue
from typing import Optional

log = logging.getLogger(__name__)

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 20777
MAX_PACKET_SIZE = 2048
QUEUE_MAXSIZE = 256


@dataclass(frozen=True)
class RawPacket:
    timestamp: float
    data: bytes


class UdpListener:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        queue_maxsize: int = QUEUE_MAXSIZE,
    ) -> None:
        self._host = host
        self._port = port
        self._queue: Queue[RawPacket] = Queue(maxsize=queue_maxsize)
        self._sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._packets_received = 0
        self._packets_dropped = 0

    @property
    def packets_received(self) -> int:
        return self._packets_received

    @property
    def packets_dropped(self) -> int:
        return self._packets_dropped

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("UdpListener already started")
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self._host, self._port))
        self._sock.settimeout(0.5)
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="UdpListener", daemon=True
        )
        self._thread.start()
        log.info("UDP listener started on %s:%d", self._host, self._port)

    def stop(self, join_timeout: float = 2.0) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=join_timeout)
            self._thread = None
        if self._sock is not None:
            self._sock.close()
            self._sock = None
        log.info(
            "UDP listener stopped. received=%d dropped=%d",
            self._packets_received,
            self._packets_dropped,
        )

    def get(self, timeout: float = 0.1) -> Optional[RawPacket]:
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None

    def _run(self) -> None:
        import time

        assert self._sock is not None
        while not self._stop_event.is_set():
            try:
                data, _ = self._sock.recvfrom(MAX_PACKET_SIZE)
            except socket.timeout:
                continue
            except OSError as exc:
                log.warning("recvfrom error: %s", exc)
                continue

            packet = RawPacket(timestamp=time.time(), data=data)
            self._packets_received += 1
            try:
                self._queue.put_nowait(packet)
            except Full:
                try:
                    self._queue.get_nowait()
                    self._queue.put_nowait(packet)
                    self._packets_dropped += 1
                except Empty:
                    self._packets_dropped += 1
