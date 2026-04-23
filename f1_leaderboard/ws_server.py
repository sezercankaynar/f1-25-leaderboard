"""WebSocket broadcast server — Snapshot'ı 10 Hz'de JSON (full/diff) pushlar.

Electron overlay client `ws://127.0.0.1:8765`'e bağlanır.
Mesaj formatı:
  {"type": "full", "data": {drivers: [...], playerIdx}}   # ilk bağlantıda
  {"type": "diff", "data": {drivers: [...changed], removed: [idx], playerIdx}}
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Dict, Optional, Set

import websockets

from .race_state import RaceStateStore
from .snapshot_codec import snapshot_to_payload, diff_payloads

log = logging.getLogger(__name__)

BROADCAST_INTERVAL = 0.2  # 5 Hz — FPS için; 10Hz akıcı ama 5Hz hâlâ gözle smooth


class WsServer:
    def __init__(
        self,
        store: RaceStateStore,
        teams_cfg: Dict[str, dict],
        host: str = '127.0.0.1',
        port: int = 8765,
    ) -> None:
        self._store = store
        self._teams_cfg = teams_cfg
        self._host = host
        self._port = port
        self._clients: Set = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event: Optional[asyncio.Event] = None
        self._last_payload: Optional[dict] = None
        self._was_active: bool = False

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run, name='WsServer', daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        if self._loop and self._stop_event:
            self._loop.call_soon_threadsafe(self._stop_event.set)

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._stop_event = asyncio.Event()
        try:
            self._loop.run_until_complete(self._main())
        finally:
            self._loop.close()

    async def _main(self) -> None:
        async with websockets.serve(self._handle, self._host, self._port):
            log.info("WS server: ws://%s:%d", self._host, self._port)
            broadcaster = asyncio.create_task(self._broadcast_loop())
            await self._stop_event.wait()
            broadcaster.cancel()
            try:
                await broadcaster
            except asyncio.CancelledError:
                pass

    async def _handle(self, ws) -> None:
        self._clients.add(ws)
        log.info("WS client connected (total=%d)", len(self._clients))
        try:
            if self._store.is_game_active() and self._last_payload is not None:
                await ws.send(json.dumps(
                    {'type': 'full', 'data': self._last_payload}
                ))
            else:
                await ws.send(json.dumps({'type': 'inactive'}))
            await ws.wait_closed()
        finally:
            self._clients.discard(ws)
            log.info("WS client disconnected (total=%d)", len(self._clients))

    async def _broadcast_loop(self) -> None:
        while True:
            await asyncio.sleep(BROADCAST_INTERVAL)
            try:
                active = self._store.is_game_active()
                if not active:
                    if self._was_active:
                        # aktif → inaktif geçişi: frontend'e bildir, full reset
                        self._was_active = False
                        self._last_payload = None
                        await self._send_to_all(json.dumps({'type': 'inactive'}))
                    continue
                # Aktif
                was = self._was_active
                self._was_active = True
                snap = self._store.snapshot()
                payload = snapshot_to_payload(snap, self._teams_cfg)
                if not was or self._last_payload is None:
                    # inaktif → aktif geçişi, veya ilk payload: full gönder
                    msg = json.dumps({'type': 'full', 'data': payload})
                    self._last_payload = payload
                else:
                    diff = diff_payloads(self._last_payload, payload)
                    if diff is None:
                        continue
                    msg = json.dumps({'type': 'diff', 'data': diff})
                    self._last_payload = payload
                await self._send_to_all(msg)
            except Exception as exc:
                log.exception("broadcast error: %s", exc)

    async def _send_to_all(self, msg: str) -> None:
        if not self._clients:
            return
        await asyncio.gather(
            *(c.send(msg) for c in list(self._clients)),
            return_exceptions=True,
        )
