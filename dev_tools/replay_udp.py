"""dump_udp.py ile alınan capture dosyasını 127.0.0.1:20777'e geri oynatır.

Kullanım:
    python dev_tools/replay_udp.py captures/race_01.bin --speed 1.0
"""
from __future__ import annotations

import argparse
import logging
import socket
import struct
import sys
import time
from pathlib import Path

RECORD_HEADER = struct.Struct("<dH")


def replay(path: Path, host: str, port: int, speed: float) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    log = logging.getLogger("replay_udp")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    start_real: float | None = None
    start_capture: float | None = None
    total = 0

    with path.open("rb") as fh:
        while True:
            head = fh.read(RECORD_HEADER.size)
            if len(head) < RECORD_HEADER.size:
                break
            ts, length = RECORD_HEADER.unpack(head)
            payload = fh.read(length)
            if len(payload) < length:
                log.warning("truncated capture at packet %d", total)
                break

            if start_real is None:
                start_real = time.time()
                start_capture = ts
            else:
                elapsed_capture = ts - start_capture
                target = start_real + elapsed_capture / speed
                sleep = target - time.time()
                if sleep > 0:
                    time.sleep(sleep)

            sock.sendto(payload, (host, port))
            total += 1

    log.info("replayed %d packets from %s", total, path)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Replay captured F1 25 UDP packets")
    ap.add_argument("capture", type=Path)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=20777)
    ap.add_argument("--speed", type=float, default=1.0, help="1.0=realtime, 2.0=2x faster")
    args = ap.parse_args()
    return replay(args.capture, args.host, args.port, args.speed)


if __name__ == "__main__":
    sys.exit(main())
