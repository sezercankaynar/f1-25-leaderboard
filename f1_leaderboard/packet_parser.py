"""F1 25 UDP paket parser.

Planlama: .planning/03-technical-spec.md, .planning/05-phases.md Faz 1-2
Dinlenen paketler: Session(1), LapData(2), Participants(4), CarStatus(7), CarDamage(10)

Struct tanımları F1 25 resmi spec'inden (MacManley/f1-25-udp README referansı) alınmış,
capture boyutları ile doğrulandı (race_01.bin üzerinde).
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

NUM_CARS = 22

HEADER_FORMAT = "<HBBBBBQfIIBB"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 29

PACKET_NAMES = {
    0: "Motion", 1: "Session", 2: "LapData", 3: "Event", 4: "Participants",
    5: "CarSetups", 6: "CarTelemetry", 7: "CarStatus", 8: "FinalClassification",
    9: "LobbyInfo", 10: "CarDamage", 11: "SessionHistory", 12: "TyreSets",
    13: "MotionEx", 14: "TimeTrial", 15: "LapPositions",
}

INTERESTED_IDS = {1, 2, 4, 7, 10}


@dataclass(frozen=True)
class PacketHeader:
    packet_format: int
    game_year: int
    game_major_version: int
    game_minor_version: int
    packet_version: int
    packet_id: int
    session_uid: int
    session_time: float
    frame_identifier: int
    overall_frame_identifier: int
    player_car_index: int
    secondary_player_car_index: int


def parse_header(data: bytes) -> Optional[PacketHeader]:
    if len(data) < HEADER_SIZE:
        return None
    try:
        return PacketHeader(*struct.unpack_from(HEADER_FORMAT, data, 0))
    except struct.error:
        return None


def packet_name(packet_id: int) -> str:
    return PACKET_NAMES.get(packet_id, f"Unknown({packet_id})")


def is_interested(packet_id: int) -> bool:
    return packet_id in INTERESTED_IDS


# --- Session (id=1) --------------------------------------------------------
# İhtiyaç duyulan alanlar paketin en başında, stabil offsetler.
# @0 weather uint8, @1 trackTemp int8, @2 airTemp int8
# rainPercentage F1 25 spec'inde mevcut ama offset'i değişken (weather_forecast
# array'inden sonra). MVP için weather enum'dan fallback kullanılır.
_SESSION_HEAD = struct.Struct("<BbbB")  # weather, trackTemp, airTemp, totalLaps


@dataclass(frozen=True)
class SessionData:
    weather: int           # 0..5
    track_temperature: int
    air_temperature: int
    total_laps: int


def parse_session(body: bytes) -> Optional[SessionData]:
    if len(body) < _SESSION_HEAD.size:
        return None
    try:
        weather, track_t, air_t, total_laps = _SESSION_HEAD.unpack_from(body, 0)
    except struct.error:
        return None
    return SessionData(weather, track_t, air_t, total_laps)


# --- LapData (id=2) --------------------------------------------------------
# Per-car 57 byte. İhtiyacımız: carPosition, currentLapNum, pitStatus, penalties
# Offset'ler (LapData struct başından itibaren):
#   lastLapTimeInMS      uint32  @ 0  (4)
#   currentLapTimeInMS   uint32  @ 4  (4)
#   sector1 MS+Min       u16+u8  @ 8  (3)
#   sector2 MS+Min       u16+u8  @11  (3)
#   deltaToCarInFront    u16+u8  @14  (3)
#   deltaToRaceLeader    u16+u8  @17  (3)
#   lapDistance          f32     @20  (4)
#   totalDistance        f32     @24  (4)
#   safetyCarDelta       f32     @28  (4)
#   carPosition          u8      @32
#   currentLapNum        u8      @33
#   pitStatus            u8      @34
#   numPitStops          u8      @35
#   sector               u8      @36
#   currentLapInvalid    u8      @37
#   penalties            u8      @38
LAPDATA_PER_CAR = 57
_LAPDATA_FIELDS = struct.Struct("<BBBBBBB")  # @32..@38, 7 uint8
# F1 24+ böldü: deltaToCarInFront = u16 ms + u8 minutes @14..@16
_LAPDATA_DELTA_FIELDS = struct.Struct("<HB")
# lastLapTime u32 @0 + currentLapTime u32 @4 + s1 u16+u8 @8 + s2 u16+u8 @11
_LAPDATA_TIMES = struct.Struct("<IIHBHB")


@dataclass(frozen=True)
class LapEntry:
    car_position: int
    current_lap_num: int
    pit_status: int        # 0=none, 1=pitting, 2=in pit area
    num_pit_stops: int
    sector: int
    current_lap_invalid: int
    penalties: int         # saniye
    delta_to_car_in_front_ms: int
    last_lap_time_ms: int          # önceki turun toplam süresi (ms)
    sector1_time_ms: int           # bu turun S1 süresi (0 = henüz tamamlanmadı)
    sector2_time_ms: int           # bu turun S2 süresi (0 = henüz tamamlanmadı)


@dataclass(frozen=True)
class LapDataPacket:
    entries: List[LapEntry]


def parse_lap_data(body: bytes) -> Optional[LapDataPacket]:
    needed = LAPDATA_PER_CAR * NUM_CARS
    if len(body) < needed:
        return None
    entries: List[LapEntry] = []
    try:
        for i in range(NUM_CARS):
            base = i * LAPDATA_PER_CAR
            (last_lap_ms, _curr_lap_ms,
             s1_ms_part, s1_min, s2_ms_part, s2_min) = _LAPDATA_TIMES.unpack_from(body, base)
            s1_total_ms = s1_min * 60_000 + s1_ms_part
            s2_total_ms = s2_min * 60_000 + s2_ms_part
            delta_ms_part, delta_min = _LAPDATA_DELTA_FIELDS.unpack_from(body, base + 14)
            delta_total_ms = delta_min * 60_000 + delta_ms_part
            fields = _LAPDATA_FIELDS.unpack_from(body, base + 32)
            entries.append(LapEntry(
                *fields,
                delta_to_car_in_front_ms=delta_total_ms,
                last_lap_time_ms=last_lap_ms,
                sector1_time_ms=s1_total_ms,
                sector2_time_ms=s2_total_ms,
            ))
    except struct.error:
        return None
    return LapDataPacket(entries)


# --- Participants (id=4) ---------------------------------------------------
# @0 numActiveCars uint8, sonra 22 × ParticipantData (57 byte/car)
# Per-car offset'ler:
#   aiControlled   u8  @0
#   driverId       u8  @1
#   networkId      u8  @2
#   teamId         u8  @3
#   myTeam         u8  @4
#   raceNumber     u8  @5
#   nationality    u8  @6
#   name           char[32] @7..38 (null-terminated UTF-8)
#   yourTelemetry  u8  @39  (+ diğer alanlar, toplam 57 byte)
PARTICIPANT_PER_CAR = 57
_PARTICIPANT_HEAD = struct.Struct("<BBBBBBB")  # 7 uint8 @0..6


@dataclass(frozen=True)
class ParticipantEntry:
    ai_controlled: int
    driver_id: int
    network_id: int
    team_id: int
    my_team: int
    race_number: int
    nationality: int
    name: str


@dataclass(frozen=True)
class ParticipantsPacket:
    num_active_cars: int
    entries: List[ParticipantEntry]


def _decode_name(raw: bytes) -> str:
    end = raw.find(b"\x00")
    if end >= 0:
        raw = raw[:end]
    try:
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return ""


def parse_participants(body: bytes) -> Optional[ParticipantsPacket]:
    if len(body) < 1 + PARTICIPANT_PER_CAR * NUM_CARS:
        return None
    num_active = body[0]
    entries: List[ParticipantEntry] = []
    try:
        for i in range(NUM_CARS):
            off = 1 + i * PARTICIPANT_PER_CAR
            ai, drv, net, team, my, race, nat = _PARTICIPANT_HEAD.unpack_from(body, off)
            name = _decode_name(body[off + 7 : off + 7 + 32])
            entries.append(ParticipantEntry(ai, drv, net, team, my, race, nat, name))
    except struct.error:
        return None
    return ParticipantsPacket(num_active, entries)


# --- CarStatus (id=7) ------------------------------------------------------
# Per-car 55 byte. İhtiyacımız: actualTyreCompound, visualTyreCompound,
# tyresAgeLaps, ersStoreEnergy
# Offset'ler:
#   tractionControl       u8 @0
#   antiLockBrakes        u8 @1
#   fuelMix               u8 @2
#   frontBrakeBias        u8 @3
#   pitLimiterStatus      u8 @4
#   fuelInTank            f32 @5
#   fuelCapacity          f32 @9
#   fuelRemainingLaps     f32 @13
#   maxRPM                u16 @17
#   idleRPM               u16 @19
#   maxGears              u8  @21
#   drsAllowed            u8  @22
#   drsActivationDistance u16 @23
#   actualTyreCompound    u8  @25
#   visualTyreCompound    u8  @26
#   tyresAgeLaps          u8  @27
#   vehicleFiaFlags       i8  @28
#   enginePowerICE        f32 @29
#   enginePowerMGUK       f32 @33
#   ersStoreEnergy        f32 @37
CARSTATUS_PER_CAR = 55
_CARSTATUS_FIELDS = struct.Struct("<BBBf")  # actual, visual, age, ersStoreEnergy

ERS_MAX_JOULES = 4_000_000.0


@dataclass(frozen=True)
class CarStatusEntry:
    actual_tyre_compound: int
    visual_tyre_compound: int
    tyres_age_laps: int
    ers_store_energy: float  # joules
    ers_deploy_mode: int     # 0=none, 1=medium, 2=hotlap, 3=overtake


@dataclass(frozen=True)
class CarStatusPacket:
    entries: List[CarStatusEntry]


def parse_car_status(body: bytes) -> Optional[CarStatusPacket]:
    if len(body) < CARSTATUS_PER_CAR * NUM_CARS:
        return None
    entries: List[CarStatusEntry] = []
    try:
        for i in range(NUM_CARS):
            base = i * CARSTATUS_PER_CAR
            actual, visual, age = struct.unpack_from("<BBB", body, base + 25)
            ers_energy = struct.unpack_from("<f", body, base + 37)[0]
            ers_mode = body[base + 41]
            entries.append(CarStatusEntry(
                actual, visual, age, ers_energy, ers_mode,
            ))
    except struct.error:
        return None
    return CarStatusPacket(entries)


# --- CarDamage (id=10) -----------------------------------------------------
# Per-car 46 byte. İhtiyacımız: tyresWear[4] — ilk 16 byte.
CARDAMAGE_PER_CAR = 46
_WEAR = struct.Struct("<ffff")


@dataclass(frozen=True)
class CarDamageEntry:
    tyre_wear: Sequence[float]  # [RL, RR, FL, FR] %


@dataclass(frozen=True)
class CarDamagePacket:
    entries: List[CarDamageEntry]


def parse_car_damage(body: bytes) -> Optional[CarDamagePacket]:
    if len(body) < CARDAMAGE_PER_CAR * NUM_CARS:
        return None
    entries: List[CarDamageEntry] = []
    try:
        for i in range(NUM_CARS):
            wear = _WEAR.unpack_from(body, i * CARDAMAGE_PER_CAR)
            entries.append(CarDamageEntry(tuple(wear)))
    except struct.error:
        return None
    return CarDamagePacket(entries)


# --- Router ----------------------------------------------------------------
@dataclass(frozen=True)
class ParsedPacket:
    header: PacketHeader
    payload: object  # SessionData | LapDataPacket | ParticipantsPacket | CarStatusPacket | CarDamagePacket


def parse(data: bytes) -> Optional[ParsedPacket]:
    header = parse_header(data)
    if header is None:
        return None
    if header.packet_id not in INTERESTED_IDS:
        return None
    body = data[HEADER_SIZE:]
    parser = _DISPATCH.get(header.packet_id)
    if parser is None:
        return None
    payload = parser(body)
    if payload is None:
        return None
    return ParsedPacket(header, payload)


_DISPATCH = {
    1: parse_session,
    2: parse_lap_data,
    4: parse_participants,
    7: parse_car_status,
    10: parse_car_damage,
}
