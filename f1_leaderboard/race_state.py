"""22 sürücünün birleştirilmiş anlık durumu + hava (immutable snapshot).

Planlama: .planning/02-architecture.md#race_statepy, .planning/03-technical-spec.md
CoW snapshot: UDP thread yeni state üretir, render thread kilitsiz okur.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, Optional, Tuple

SECTOR_NONE = 0     # henüz tamamlanmadı (gri)
SECTOR_YELLOW = 1   # tamamlandı, kayıt değil (F1: normal completion)
SECTOR_PURPLE = 2   # field-wide overall best (session best)
SECTOR_GREEN = 3    # kendi PB'sini kırdı (personal best, improvement)

# Tur sonunda 3 sektör rengini ne kadar göstermeye devam edeceğimiz
# (yeni turun ilk sektörü tamamlanana kadar ya da bu süre dolana kadar — hangisi önce)
LAP_COLOR_PERSIST_SEC = 7.0

from .packet_parser import (
    CarDamagePacket,
    CarStatusPacket,
    LapDataPacket,
    ParsedPacket,
    ParticipantsPacket,
    SessionData,
    NUM_CARS,
)

ERS_MAX_JOULES = 4_000_000.0

# weather enum → yağış yüzdesi fallback
_WEATHER_TO_RAIN = {0: 0, 1: 0, 2: 5, 3: 35, 4: 70, 5: 95}


@dataclass(frozen=True)
class Driver:
    index: int
    position: int = 0
    name: str = ""
    team_id: int = 255
    ai_controlled: int = 1

    ers_percent: float = 0.0
    ers_deploy_mode: int = 0           # 0=none, 1=medium, 2=hotlap, 3=overtake
    actual_compound: int = 0
    visual_compound: int = 0
    tyre_age_laps: int = 0
    tyre_wear_avg: float = 0.0
    tyre_wear_max: float = 0.0

    current_lap: int = 0
    current_sector: int = 0            # 0..2 (F1 25 LapData.sector u8)
    pit_status: int = 0
    num_pit_stops: int = 0
    penalties: int = 0
    current_lap_invalid: int = 0
    delta_to_ahead_ms: Optional[int] = None  # None = lider veya veri yok

    # Sektör takibi — PB/overall-best karşılaştırması için
    pb_s1_ms: int = 0                  # sürücünün şu ana kadarki en hızlı S1
    pb_s2_ms: int = 0
    pb_s3_ms: int = 0
    current_lap_s1_ms: int = 0         # bu lap içinde görülen son S1 (PB değil, O lap)
    current_lap_s2_ms: int = 0         # bu lap içinde görülen son S2
    sector_status: Tuple[int, int, int] = (0, 0, 0)  # 0=gri / 1=sarı / 2=mor / 3=yeşil
    sector_display_until: float = 0.0  # monotonic timestamp — tur sonu renk persist'i
    _last_seen_lap: int = 0            # tur değişimi tespiti için internal


@dataclass(frozen=True)
class Weather:
    weather_code: int = 0
    track_temp_c: int = 0
    air_temp_c: int = 0
    rain_percent: int = 0
    total_laps: int = 0


@dataclass(frozen=True)
class Snapshot:
    drivers: Tuple[Driver, ...] = field(
        default_factory=lambda: tuple(Driver(index=i) for i in range(NUM_CARS))
    )
    weather: Weather = field(default_factory=Weather)
    player_car_index: int = 0
    num_active_cars: int = 0

    # Field-wide en iyi sektör süreleri (tüm sürücülerin tümünden)
    overall_best_s1_ms: int = 0
    overall_best_s2_ms: int = 0
    overall_best_s3_ms: int = 0


def _team_abbr(name: str) -> str:
    """Soyad ilk 3 harfi; yoksa ad ilk 3. Fallback '???'."""
    name = name.strip()
    if not name:
        return "???"
    parts = name.split()
    base = parts[-1] if len(parts) > 1 else parts[0]
    return base[:3].upper()


class RaceStateStore:
    """Thread-safe snapshot container (reference-swap CoW).

    Ayrıca "oyun aktif mi" tespit eder: UDP paket header'ındaki
    session_time'ın duvar-saati zamanında ilerlemesine bakar. Oyun duraklı /
    menüde / garage setup ekranında session_time sabit kalır (veya UDP hiç
    gelmez), dolayısıyla is_game_active() False döner.
    """

    def __init__(self) -> None:
        self._current = Snapshot()
        self._lock = threading.Lock()
        self._last_session_time: float = -1.0
        self._last_session_time_change_at: float = 0.0

    def snapshot(self) -> Snapshot:
        return self._current  # reference read atomic

    def apply(self, parsed: ParsedPacket) -> None:
        with self._lock:
            st = parsed.header.session_time
            if st != self._last_session_time:
                self._last_session_time = st
                self._last_session_time_change_at = time.monotonic()
            self._current = self._merge(self._current, parsed)

    def is_game_active(self, stale_threshold: float = 0.6) -> bool:
        if self._last_session_time_change_at == 0.0:
            return False  # hiç paket gelmedi
        return (time.monotonic() - self._last_session_time_change_at) < stale_threshold

    @staticmethod
    def _merge(state: Snapshot, parsed: ParsedPacket) -> Snapshot:
        pid = parsed.header.packet_id
        player_idx = parsed.header.player_car_index
        if pid == 1:
            return _apply_session(state, parsed.payload, player_idx)
        if pid == 2:
            return _apply_lap_data(state, parsed.payload, player_idx)
        if pid == 4:
            return _apply_participants(state, parsed.payload, player_idx)
        if pid == 7:
            return _apply_car_status(state, parsed.payload, player_idx)
        if pid == 10:
            return _apply_car_damage(state, parsed.payload, player_idx)
        return state


def _apply_session(state: Snapshot, s: SessionData, player_idx: int) -> Snapshot:
    rain = _WEATHER_TO_RAIN.get(s.weather, 0)
    return replace(
        state,
        weather=Weather(
            weather_code=s.weather,
            track_temp_c=s.track_temperature,
            air_temp_c=s.air_temperature,
            rain_percent=rain,
            total_laps=s.total_laps,
        ),
        player_car_index=player_idx,
    )


def _status_for(s_ms: int, pb_ms: int, ob_ms: int) -> int:
    """F1 broadcast convention sektör rengi.

    Caller bu fonksiyonu pb ve ob güncellenmiş durumda çağırır (yani yeni
    rekor varsa pb_ms == s_ms olur).

    Öncelik:
      - s_ms <= 0               → 0 gri (henüz tamamlanmadı)
      - ob > 0 ve s_ms <= ob    → 2 mor (overall best)
      - pb > 0 ve s_ms <= pb    → 3 yeşil (personal best, improvement)
      - aksi halde              → 1 sarı (tamamlandı, kayıt değil)
    """
    if s_ms <= 0:
        return SECTOR_NONE
    if ob_ms > 0 and s_ms <= ob_ms:
        return SECTOR_PURPLE
    if pb_ms > 0 and s_ms <= pb_ms:
        return SECTOR_GREEN
    return SECTOR_YELLOW


def _apply_lap_data(state: Snapshot, p: LapDataPacket, player_idx: int) -> Snapshot:
    now = time.monotonic()
    drivers = list(state.drivers)
    ob_s1 = state.overall_best_s1_ms
    ob_s2 = state.overall_best_s2_ms
    ob_s3 = state.overall_best_s3_ms

    for i, entry in enumerate(p.entries):
        d = drivers[i]
        delta = None if entry.car_position == 1 else entry.delta_to_car_in_front_ms
        new_s1 = entry.sector1_time_ms
        new_s2 = entry.sector2_time_ms
        new_lap = entry.current_lap_num
        last_lap_ms = entry.last_lap_time_ms

        pb_s1 = d.pb_s1_ms
        pb_s2 = d.pb_s2_ms
        pb_s3 = d.pb_s3_ms
        cur_s1 = d.current_lap_s1_ms
        cur_s2 = d.current_lap_s2_ms
        status = d.sector_status
        display_until = d.sector_display_until

        # 1a) Yarış restart — lap GERİ gitti
        if d._last_seen_lap > 0 and new_lap < d._last_seen_lap:
            pb_s1 = pb_s2 = pb_s3 = 0
            cur_s1 = cur_s2 = 0
            status = (SECTOR_NONE, SECTOR_NONE, SECTOR_NONE)
            display_until = 0.0
        # 1b) Normal tur değişimi (ileri) — S3 rengi hesapla, persist başlat
        elif (d._last_seen_lap > 0 and new_lap > d._last_seen_lap
              and last_lap_ms > 0):
            s3_color = SECTOR_NONE
            if cur_s1 > 0 and cur_s2 > 0:
                actual_s3 = last_lap_ms - cur_s1 - cur_s2
                if actual_s3 > 0:
                    if pb_s3 == 0 or actual_s3 < pb_s3:
                        pb_s3 = actual_s3
                    if ob_s3 == 0 or actual_s3 < ob_s3:
                        ob_s3 = actual_s3
                    s3_color = _status_for(actual_s3, pb_s3, ob_s3)
            # Biten turun 3 sektör rengini göstermeye devam et
            status = (status[0], status[1], s3_color)
            display_until = now + LAP_COLOR_PERSIST_SEC
            # cur_s1/s2 sıfırla — yeni lap'in s1 completion tespiti için
            cur_s1 = 0
            cur_s2 = 0

        # 2) Persist süresi dolduysa temizle (yeni lap'in S1'i henüz gelmediyse)
        if display_until > 0 and now >= display_until:
            status = (SECTOR_NONE, SECTOR_NONE, SECTOR_NONE)
            display_until = 0.0

        skip = entry.pit_status > 0

        # 3) S1 — yeni lap'in ilk sektörü tamamlandığında persist'i sonlandır
        if new_s1 > 0:
            if display_until > 0:
                # Persist hâlâ aktif ama yeni lap'in S1'i geldi — eski display'i
                # at, sadece yeni S1'i göster (S2/S3 eski lap'ten kalma olurdu)
                status = (SECTOR_NONE, SECTOR_NONE, SECTOR_NONE)
                display_until = 0.0
            cur_s1 = new_s1
            if pb_s1 == 0 or new_s1 < pb_s1:
                pb_s1 = new_s1
            if ob_s1 == 0 or new_s1 < ob_s1:
                ob_s1 = new_s1
            if not skip:
                status = (_status_for(new_s1, pb_s1, ob_s1), status[1], status[2])

        # 4) S2
        if new_s2 > 0:
            cur_s2 = new_s2
            if pb_s2 == 0 or new_s2 < pb_s2:
                pb_s2 = new_s2
            if ob_s2 == 0 or new_s2 < ob_s2:
                ob_s2 = new_s2
            if not skip:
                status = (status[0], _status_for(new_s2, pb_s2, ob_s2), status[2])

        drivers[i] = replace(
            d,
            position=entry.car_position,
            current_lap=new_lap,
            current_sector=entry.sector,
            pit_status=entry.pit_status,
            num_pit_stops=entry.num_pit_stops,
            penalties=entry.penalties,
            current_lap_invalid=entry.current_lap_invalid,
            delta_to_ahead_ms=delta,
            pb_s1_ms=pb_s1,
            pb_s2_ms=pb_s2,
            pb_s3_ms=pb_s3,
            current_lap_s1_ms=cur_s1,
            current_lap_s2_ms=cur_s2,
            sector_status=status,
            sector_display_until=display_until,
            _last_seen_lap=new_lap,
        )

    return replace(
        state,
        drivers=tuple(drivers),
        player_car_index=player_idx,
        overall_best_s1_ms=ob_s1,
        overall_best_s2_ms=ob_s2,
        overall_best_s3_ms=ob_s3,
    )


def _apply_participants(
    state: Snapshot, p: ParticipantsPacket, player_idx: int
) -> Snapshot:
    drivers = list(state.drivers)
    for i, entry in enumerate(p.entries):
        drivers[i] = replace(
            drivers[i],
            name=entry.name,
            team_id=entry.team_id,
            ai_controlled=entry.ai_controlled,
        )
    return replace(
        state,
        drivers=tuple(drivers),
        player_car_index=player_idx,
        num_active_cars=p.num_active_cars,
    )


def _apply_car_status(
    state: Snapshot, p: CarStatusPacket, player_idx: int
) -> Snapshot:
    drivers = list(state.drivers)
    for i, entry in enumerate(p.entries):
        ers_pct = max(0.0, min(1.0, entry.ers_store_energy / ERS_MAX_JOULES))
        drivers[i] = replace(
            drivers[i],
            ers_percent=ers_pct,
            ers_deploy_mode=entry.ers_deploy_mode,
            actual_compound=entry.actual_tyre_compound,
            visual_compound=entry.visual_tyre_compound,
            tyre_age_laps=entry.tyres_age_laps,
        )
    return replace(state, drivers=tuple(drivers), player_car_index=player_idx)


def _apply_car_damage(
    state: Snapshot, p: CarDamagePacket, player_idx: int
) -> Snapshot:
    drivers = list(state.drivers)
    for i, entry in enumerate(p.entries):
        wear = entry.tyre_wear
        avg = sum(wear) / 4.0
        mx = max(wear)
        drivers[i] = replace(drivers[i], tyre_wear_avg=avg, tyre_wear_max=mx)
    return replace(state, drivers=tuple(drivers), player_car_index=player_idx)
