"""Capture dosyasını parse ederek son snapshot'ın insan okunur özetini basar."""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from f1_leaderboard.packet_parser import parse
from f1_leaderboard.race_state import RaceStateStore

REC = struct.Struct("<dH")

_COMPOUND = {16: "S", 17: "M", 18: "H", 7: "I", 8: "W"}


def run(path: Path) -> int:
    store = RaceStateStore()
    good = bad = 0
    with path.open("rb") as fh:
        while True:
            head = fh.read(REC.size)
            if len(head) < REC.size:
                break
            _ts, n = REC.unpack(head)
            data = fh.read(n)
            if len(data) < n:
                break
            parsed = parse(data)
            if parsed is None:
                bad += 1
                continue
            good += 1
            store.apply(parsed)

    snap = store.snapshot()
    print(f"parsed_ok={good} skipped={bad}")
    print(
        f"weather: code={snap.weather.weather_code} "
        f"track={snap.weather.track_temp_c}°C air={snap.weather.air_temp_c}°C "
        f"rain={snap.weather.rain_percent}% total_laps={snap.weather.total_laps}"
    )
    print(f"player_car_index={snap.player_car_index} active={snap.num_active_cars}")
    print(f"{'pos':>3} {'idx':>3} {'name':<16} {'team':>4} {'sec':>3} {'delta_ms':>9} "
          f"{'ers%':>5} {'tyre':>5} {'age':>3} {'wear':>5} {'lap':>3} {'pit':>3}")
    by_pos = sorted(snap.drivers, key=lambda d: (d.position if d.position > 0 else 99))
    for d in by_pos:
        if d.position == 0 and not d.name:
            continue
        c = _COMPOUND.get(d.visual_compound, "?")
        delta_s = "" if d.delta_to_ahead_ms is None else str(d.delta_to_ahead_ms)
        print(f"{d.position:>3} {d.index:>3} {d.name[:16]:<16} {d.team_id:>4} "
              f"{d.current_sector:>3} {delta_s:>9} "
              f"{d.ers_percent*100:>5.1f} {c:>5} {d.tyre_age_laps:>3} "
              f"{d.tyre_wear_avg:>5.1f} {d.current_lap:>3} {d.pit_status:>3}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("capture", type=Path)
    args = ap.parse_args()
    return run(args.capture)


if __name__ == "__main__":
    sys.exit(main())
