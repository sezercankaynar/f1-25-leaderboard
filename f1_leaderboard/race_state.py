"""22 sürücünün birleştirilmiş anlık durumu + hava (immutable snapshot).

Planlama: .planning/02-architecture.md#race_statepy, .planning/03-technical-spec.md
CoW snapshot: UDP thread yeni state üretir, render thread kilitsiz okur.
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, Optional, Tuple

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


def _team_abbr(name: str) -> str:
    """Soyad ilk 3 harfi; yoksa ad ilk 3. Fallback '???'."""
    name = name.strip()
    if not name:
        return "???"
    parts = name.split()
    base = parts[-1] if len(parts) > 1 else parts[0]
    return base[:3].upper()


class RaceStateStore:
    """Thread-safe snapshot container (reference-swap CoW)."""

    def __init__(self) -> None:
        self._current = Snapshot()
        self._lock = threading.Lock()

    def snapshot(self) -> Snapshot:
        return self._current  # reference read atomic

    def apply(self, parsed: ParsedPacket) -> None:
        with self._lock:
            self._current = self._merge(self._current, parsed)

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


def _apply_lap_data(state: Snapshot, p: LapDataPacket, player_idx: int) -> Snapshot:
    drivers = list(state.drivers)
    for i, entry in enumerate(p.entries):
        delta = None if entry.car_position == 1 else entry.delta_to_car_in_front_ms
        drivers[i] = replace(
            drivers[i],
            position=entry.car_position,
            current_lap=entry.current_lap_num,
            current_sector=entry.sector,
            pit_status=entry.pit_status,
            num_pit_stops=entry.num_pit_stops,
            penalties=entry.penalties,
            current_lap_invalid=entry.current_lap_invalid,
            delta_to_ahead_ms=delta,
        )
    return replace(state, drivers=tuple(drivers), player_car_index=player_idx)


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
