"""F1 25 UDP paketlerini yakala ve binary dosyaya kaydet (replay için).

Kullanım:
    python dev_tools/dump_udp.py --output captures/race_01.bin --duration 60

Dosya formatı (her paket için ardışık):
    [timestamp: float64 little-endian]
    [length:    uint16  little-endian]
    [bytes:     length byte]
"""
from __future__ import annotations

import argparse
import logging
import os
import struct
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from f1_leaderboard.packet_parser import packet_name, parse_header
from f1_leaderboard.udp_listener import UdpListener

RECORD_HEADER = struct.Struct("<dH")


def run(output: Path, duration: float, port: int) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    log = logging.getLogger("dump_udp")

    output.parent.mkdir(parents=True, exist_ok=True)
    counters: Counter[int] = Counter()
    total = 0

    listener = UdpListener(port=port)
    listener.start()

    deadline = time.time() + duration
    try:
        with output.open("wb") as fh:
            while time.time() < deadline:
                packet = listener.get(timeout=0.25)
                if packet is None:
                    continue
                fh.write(RECORD_HEADER.pack(packet.timestamp, len(packet.data)))
                fh.write(packet.data)
                total += 1
                header = parse_header(packet.data)
                if header is not None:
                    counters[header.packet_id] += 1
    except KeyboardInterrupt:
        log.info("interrupted")
    finally:
        listener.stop()

    log.info("captured %d packets in %d bytes", total, os.path.getsize(output))
    for pid in sorted(counters):
        log.info("  %-20s id=%2d count=%d", packet_name(pid), pid, counters[pid])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="F1 25 UDP capture tool")
    ap.add_argument("--output", type=Path, default=Path("captures/capture.bin"))
    ap.add_argument("--duration", type=float, default=30.0, help="saniye")
    ap.add_argument("--port", type=int, default=20777)
    args = ap.parse_args()
    return run(args.output, args.duration, args.port)


if __name__ == "__main__":
    sys.exit(main())
