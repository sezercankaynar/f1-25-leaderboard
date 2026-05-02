"""Snapshot → JSON payload mapping + per-driver diff.

Tasarım (Claude Design Classic Broadcast) sürücü şeması:
  {idx, pos, code, name, team, teamColor, sectors[3], gap, compound, wear,
   laps, ers, ersMode, isPlayer, pitStatus}

- team: geçici design kodu (APX/VLK/...); 4b-3'te gerçek F1 team name ile değişecek
- sectors: [0,0,0] başlangıç, aktif sektör kadar 1 (PB placeholder). 4b-4'te
  SessionHistory packet ile PB/overall-best/improving renk durumları tam işlenecek
- ersMode: "M" default; 4b-4'te CarStatus @41 ersDeployMode parse edilecek
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .race_state import Driver, Snapshot

# F1 25 sessionType enum → header label (Türkçe)
# F1 25 spec'i F1 24'e göre Sprint Shootout (10-14) varyantlarını ekleyince
# Race kodu 10 → 15'e kaydı. Bilinmeyen değerler '— — —' fallback'ine düşer.
_SESSION_TYPE_LABEL: Dict[int, str] = {
    # Practice
    1: 'PRATİK', 2: 'PRATİK', 3: 'PRATİK', 4: 'PRATİK',
    # Qualifying
    5: 'SIRALAMA', 6: 'SIRALAMA', 7: 'SIRALAMA', 8: 'SIRALAMA', 9: 'SIRALAMA',
    # Sprint Shootout (F1 25'te eklendi)
    10: 'SPRINT SIRALAMA', 11: 'SPRINT SIRALAMA', 12: 'SPRINT SIRALAMA',
    13: 'SPRINT SIRALAMA', 14: 'SPRINT SIRALAMA',
    # Race (F1 25'te 15'ten başlıyor)
    15: 'YARIŞ', 16: 'YARIŞ', 17: 'YARIŞ',
    # Time Trial
    18: 'TIME TRIAL',
    # Sprint (F1 25'te bazı versiyonlarda 19 olarak rapor edilir)
    19: 'SPRINT',
}

# F1 weather enum → tasarım weather string
_WEATHER_TO_LABEL: Dict[int, str] = {
    0: 'dry', 1: 'dry', 2: 'cloudy', 3: 'lightrain', 4: 'heavyrain', 5: 'storm',
}

TEAM_ID_TO_CODE: Dict[int, str] = {
    0: 'VLK', 1: 'APX', 2: 'TRN', 3: 'NRD', 4: 'VRT',
    5: 'SLC', 6: 'MRD', 7: 'HLX', 8: 'ORB', 9: 'KRN',
}

COMPOUND_MAP: Dict[int, str] = {
    16: 'S', 17: 'M', 18: 'H',
    7:  'I', 8:  'W',
}

# F1 25 ersDeployMode → design letter (N=off, M=medium, H=hotlap, O=overtake)
ERS_MODE_MAP: Dict[int, str] = {0: 'N', 1: 'M', 2: 'H', 3: 'O'}


def _derive_code(name: str) -> str:
    name = name.strip()
    if not name:
        return '---'
    parts = name.split()
    base = parts[-1] if len(parts) > 1 else parts[0]
    return base[:3].upper()


def _format_gap(delta_ms: Optional[int], position: int) -> str:
    if position == 1:
        return 'LEADER'
    if delta_ms is None or delta_ms == 0:
        return '—'
    seconds = delta_ms / 1000.0
    return f'+{seconds:.3f}'


def _sector_status_list(d: Driver) -> List[int]:
    return list(d.sector_status)


def _driver_dict(
    d: Driver,
    player_idx: int,
    teams_cfg: Dict[str, dict],
    overall_best_lap_ms: int,
) -> dict:
    team_meta = teams_cfg.get(str(d.team_id))
    team_color = team_meta['color'] if team_meta else '#808080'
    is_fastest = (
        overall_best_lap_ms > 0
        and d.best_lap_ms > 0
        and d.best_lap_ms == overall_best_lap_ms
    )
    return {
        'idx': d.index,
        'pos': d.position,
        'code': _derive_code(d.name),
        'name': d.name,
        'team': TEAM_ID_TO_CODE.get(d.team_id, 'APX'),
        'teamId': d.team_id,
        'teamColor': team_color,
        'sectors': _sector_status_list(d),
        'gap': _format_gap(d.delta_to_ahead_ms, d.position),
        'compound': COMPOUND_MAP.get(d.visual_compound, 'S'),
        'wear': round(d.tyre_wear_avg, 1),
        'laps': d.tyre_age_laps,
        'ers': round(d.ers_percent * 100, 1),
        'ersMode': ERS_MODE_MAP.get(d.ers_deploy_mode, 'N'),
        'isPlayer': d.index == player_idx,
        'pitStatus': d.pit_status,
        'fastestLap': is_fastest,
    }


def _format_time_left(seconds: int) -> str:
    if seconds <= 0:
        return ''
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f'{h}:{m:02d}:{s:02d}'
    return f'{m}:{s:02d}'


def _session_payload(snap: Snapshot) -> dict:
    pidx = snap.player_car_index
    player = snap.drivers[pidx] if 0 <= pidx < len(snap.drivers) else None
    return {
        'type': _SESSION_TYPE_LABEL.get(snap.session_type, '— — —'),
        'lap': player.current_lap if player else 0,
        'totalLaps': snap.weather.total_laps,
        'timeLeft': _format_time_left(snap.session_time_left),
        'trackTemp': snap.weather.track_temp_c,
        'airTemp': snap.weather.air_temp_c,
        'rainChance': snap.weather.rain_percent,
        'weather': _WEATHER_TO_LABEL.get(snap.weather.weather_code, 'dry'),
    }


def snapshot_to_payload(snap: Snapshot, teams_cfg: Dict[str, dict]) -> dict:
    drivers = [
        _driver_dict(d, snap.player_car_index, teams_cfg, snap.overall_best_lap_ms)
        for d in snap.drivers
        if d.position > 0
    ]
    drivers.sort(key=lambda x: x['pos'])
    return {
        'drivers': drivers,
        'playerIdx': snap.player_car_index,
        'session': _session_payload(snap),
    }


def diff_payloads(prev: dict, curr: dict) -> Optional[dict]:
    if prev == curr:
        return None
    prev_by_idx = {d['idx']: d for d in prev.get('drivers', [])}
    changed = [d for d in curr.get('drivers', [])
               if prev_by_idx.get(d['idx']) != d]
    player_changed = prev.get('playerIdx') != curr.get('playerIdx')
    removed_idx = [idx for idx in prev_by_idx
                   if idx not in {d['idx'] for d in curr.get('drivers', [])}]
    session_changed = prev.get('session') != curr.get('session')
    if not changed and not player_changed and not removed_idx and not session_changed:
        return None
    out: dict = {
        'drivers': changed,
        'removed': removed_idx,
        'playerIdx': curr.get('playerIdx'),
    }
    if session_changed:
        out['session'] = curr.get('session')
    return out
