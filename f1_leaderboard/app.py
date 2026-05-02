"""Backend giriş noktası: UDP listener + parser pump + WebSocket broadcast.

Frontend (Electron/React) ayrı prosestir — ws://127.0.0.1:8765'e bağlanır.
Qt/PyQt bu dosyadan kaldırıldı (F4b — Electron geçişi, 2026-04-23).
Legacy Qt kodları (`overlay_window.py`, `leaderboard_widget.py`,
`weather_panel_widget.py`) henüz silinmedi ama kullanılmıyor.
"""
from __future__ import annotations

import json
import logging
import signal
import sys
import threading
import time
from pathlib import Path

from .packet_parser import parse
from .race_state import RaceStateStore
from .udp_listener import UdpListener
from .ws_server import WsServer

log = logging.getLogger(__name__)


def _resolve_config_dir() -> Path:
    """PyInstaller ile paketlenmiş exe'de config/ exe'nin yanında olur;
    dev'de proje kök dizininde. sys.frozen True iken sys.executable kullan."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "config"
    return Path(__file__).resolve().parent.parent / "config"


CONFIG_DIR = _resolve_config_dir()


def _load_teams() -> dict:
    with (CONFIG_DIR / "teams.json").open(encoding="utf-8") as fh:
        return {k: v for k, v in json.load(fh).items() if not k.startswith("_")}


def _pump_loop(
    listener: UdpListener,
    store: RaceStateStore,
    stop: threading.Event,
    stats: dict,
) -> None:
    while not stop.is_set():
        packet = listener.get(timeout=0.1)
        if packet is None:
            continue
        stats["recv"] = stats.get("recv", 0) + 1
        parsed = parse(packet.data)
        if parsed is not None:
            stats["parsed"] = stats.get("parsed", 0) + 1
            pid = parsed.header.packet_id
            stats["by_pid"][pid] = stats["by_pid"].get(pid, 0) + 1
            store.apply(parsed)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    teams_cfg = _load_teams()

    store = RaceStateStore()
    listener = UdpListener()
    listener.start()

    stop_event = threading.Event()
    stats: dict = {"recv": 0, "parsed": 0, "by_pid": {}}
    pump = threading.Thread(
        target=_pump_loop, args=(listener, store, stop_event, stats),
        name="PumpLoop", daemon=True,
    )
    pump.start()

    ws = WsServer(store, teams_cfg)
    ws.start()

    def _shutdown(*_) -> None:
        log.info("shutting down…")
        stop_event.set()
        listener.stop()
        ws.stop()
        pump.join(timeout=1.0)

    signal.signal(signal.SIGINT, lambda *_: (_shutdown(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda *_: (_shutdown(), sys.exit(0)))

    log.info("backend running — Ctrl+C to stop")
    try:
        while not stop_event.is_set():
            time.sleep(2.0)
            snap = store.snapshot()
            with_pos = sum(1 for d in snap.drivers if d.position > 0)
            with_name = sum(1 for d in snap.drivers if d.name)
            pidx = snap.player_car_index
            p = snap.drivers[pidx] if 0 <= pidx < len(snap.drivers) else None
            ers_info = (
                f"ersMode={p.ers_deploy_mode} ers={p.ers_percent*100:.1f}% "
                f"compound={p.visual_compound} wear={p.tyre_wear_avg:.1f}%"
                if p else "no player"
            )
            sec_info = (
                f"lap={p.current_lap} sec_idx={p.current_sector} "
                f"inv={p.current_lap_invalid} pit={p.pit_status} "
                f"status={p.sector_status} "
                f"cur=({p.current_lap_s1_ms},{p.current_lap_s2_ms}) "
                f"pb=({p.pb_s1_ms},{p.pb_s2_ms},{p.pb_s3_ms}) "
                f"ob=({snap.overall_best_s1_ms},{snap.overall_best_s2_ms},{snap.overall_best_s3_ms})"
                if p else ""
            )
            sess_info = (
                f"sess_type={snap.session_type} laps_total={snap.weather.total_laps} "
                f"time_left={snap.session_time_left}s "
                f"track={snap.weather.track_temp_c}C air={snap.weather.air_temp_c}C "
                f"weather_code={snap.weather.weather_code}"
            )
            log.info(
                "recv=%d parsed=%d | pos>0=%d named=%d | %s | player[%d] %s | %s",
                stats["recv"], stats["parsed"],
                with_pos, with_name, sess_info, pidx, ers_info, sec_info,
            )
    except KeyboardInterrupt:
        _shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
