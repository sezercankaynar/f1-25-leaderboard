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


def _driver_dict(d: Driver, player_idx: int, teams_cfg: Dict[str, dict]) -> dict:
    team_meta = teams_cfg.get(str(d.team_id))
    team_color = team_meta['color'] if team_meta else '#808080'
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
    }


def snapshot_to_payload(snap: Snapshot, teams_cfg: Dict[str, dict]) -> dict:
    drivers = [
        _driver_dict(d, snap.player_car_index, teams_cfg)
        for d in snap.drivers
        if d.position > 0
    ]
    drivers.sort(key=lambda x: x['pos'])
    return {
        'drivers': drivers,
        'playerIdx': snap.player_car_index,
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
    if not changed and not player_changed and not removed_idx:
        return None
    return {
        'drivers': changed,
        'removed': removed_idx,
        'playerIdx': curr.get('playerIdx'),
    }
