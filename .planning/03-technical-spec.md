# 03 — Teknik Spesifikasyon

## 1. UDP Paket Parser Detayları

### 1.1 Paket Header (tüm paketlerin ortak ilk 29 byte'ı)

F1 23 header referansı (F1 25'te aynı kalma beklentisiyle — araştırma fazında doğrulanacak):

```python
@dataclass
class PacketHeader:
    packet_format: int          # uint16  — 2025 beklenir
    game_year: int              # uint8
    game_major_version: int     # uint8
    game_minor_version: int     # uint8
    packet_version: int         # uint8
    packet_id: int              # uint8  — ROUTER BU ALANA GÖRE
    session_uid: int            # uint64
    session_time: float         # float32
    frame_identifier: int       # uint32
    overall_frame_identifier: int  # uint32 (F1 23+)
    player_car_index: int       # uint8  — bizim aracımız
    secondary_player_car_index: int  # uint8
```

**Python struct format string'i:** `"<HBBBBBQfIIBB"` — little-endian

### 1.2 Router Mantığı

```python
PACKET_HANDLERS = {
    1: parse_session,
    2: parse_lap_data,
    4: parse_participants,
    7: parse_car_status,
    10: parse_car_damage,
}

def dispatch(raw_bytes: bytes) -> None:
    header = parse_header(raw_bytes[:29])
    handler = PACKET_HANDLERS.get(header.packet_id)
    if handler is None:
        return  # ignored packet, no cost
    parsed = handler(raw_bytes[29:], header)
    race_state.apply(parsed)
```

### 1.3 Her Paketin Struct Tanımları

**Session Packet (id=1)** — ihtiyaç duyulan alanlar:
```python
# Offset'ler header sonrası
weather: uint8                  # 0..5 enum
track_temperature: int8         # °C
air_temperature: int8           # °C
total_laps: uint8
track_length: uint16
# ... (diğer alanlar skip edilebilir)
# Array alanı:
num_weather_forecast_samples: uint8
weather_forecast_samples: [64 x 8 byte]  # F1 23'te 56 örnek, F1 25'te farklı olabilir
# ... (daha aşağıda)
rain_percentage: int8           # F1 24+ — araştırma fazında doğrula
```

**Aksiyon:** Parser sadece ihtiyaç duyulan alanları okumak için `struct.unpack_from(format, data, offset)` kullansın. Tüm paketi açmak gereksiz CPU.

**Lap Data Packet (id=2)** — 22 sürücü için `LapData[22]` dizisi:
```python
@dataclass
class LapData:
    # sadece kullanılanlar:
    car_position: uint8         # Live position
    current_lap_num: uint8
    pit_status: uint8           # 0=none, 1=pitting, 2=in pit area
    penalties: uint8            # saniye cinsinden toplam ceza
    num_pit_stops: uint8
    # ... gerisi skip
```

Sabit boyutlu 22x struct array → `struct.iter_unpack` ideal.

**Participants Packet (id=4)** — 22 sürücü için dizi:
```python
@dataclass
class ParticipantData:
    ai_controlled: uint8
    driver_id: uint8            # built-in driver
    network_id: uint8
    team_id: uint8              # map to teamName + color
    my_team: uint8
    race_number: uint8
    nationality: uint8
    name: bytes[32]             # UTF-8 null-terminated
    # name'den 3-harf kısaltma türet: "Max Verstappen" → "VER"
```

**3-harf kısaltma türetme kuralı:**
- Driver DB'de tanımlı ise doğrudan kullan (örn. `VER, HAM, LEC`)
- Yoksa: soyadın ilk 3 harfi, büyük harf
- Ad tek kelime ise: ilk 3 harfi

**Car Status Packet (id=7)** — 22 sürücü için dizi:
```python
@dataclass
class CarStatusData:
    # 20+ alanın sadece bunları:
    fuel_remaining_laps: float32
    ers_store_energy: float32   # Joules — max ~4 MJ (4,000,000)
    ers_deploy_mode: uint8
    actual_tyre_compound: uint8
    visual_tyre_compound: uint8
    tyres_age_laps: uint8       # KRİTİK — bu alanın F1 25'te var olduğunu doğrula
    vehicle_fia_flags: int8
    # ... gerisi skip
```

**ERS yüzde hesabı:**
```python
ers_percent = ers_store_energy / 4_000_000.0  # 4 MJ max
ers_percent = max(0.0, min(1.0, ers_percent))
```

**Car Damage Packet (id=10)** — 22 sürücü için dizi:
```python
@dataclass
class CarDamageData:
    tyres_wear: float32[4]      # [RL, RR, FL, FR] % — 0..100
    tyres_damage: uint8[4]
    # ... diğer hasar alanları skip
```

**Lastik aşınma birleştirmesi:**
```python
tyre_wear_avg = sum(tyres_wear) / 4.0
tyre_wear_max = max(tyres_wear)
# UI'da avg gösterilecek, renk threshold'u max'a göre (en kötü lastik)
```

## 2. Hesaplanan Alanlar

### 2.1 Gap (Öndeki sürücüye zaman farkı)
- **Not:** Bu MVP'de istenmedi (Q&A'da seçilmedi), spec'e yazmıyoruz. Eklemek istenirse M7 olarak gelsin.

### 2.2 Takım rengi
```python
TEAM_COLORS = load_json("config/teams.json")
color = TEAM_COLORS[team_id]["color"]
```

### 2.3 Lastik rozeti metni ve rengi
```python
COMPOUND_MAP = {
    16: ("S", "#FF0000"),  # Soft kırmızı
    17: ("M", "#FFD700"),  # Medium sarı
    18: ("H", "#FFFFFF"),  # Hard beyaz
    7:  ("I", "#00C853"),  # Inter yeşil
    8:  ("W", "#2196F3"),  # Wet mavi
}
# Kullanım:
badge_letter, badge_color = COMPOUND_MAP.get(visual_compound, ("?", "#888"))
```

### 2.4 Lastik aşınma renk threshold'u
```python
def wear_color(wear_pct: float) -> str:
    if wear_pct < 30: return "#00E676"   # yeşil
    if wear_pct < 60: return "#FFEB3B"   # sarı
    if wear_pct < 85: return "#FF9800"   # turuncu
    return "#F44336"                      # kırmızı
```

### 2.5 ERS bar renk gradient'i
```python
# Mor-mavi arası — F1 resmi ERS rengi
def ers_color(percent: float) -> str:
    if percent > 0.66: return "#7B1FA2"  # dolu, mor
    if percent > 0.33: return "#3F51B5"  # orta, mavi
    return "#607D8B"                      # düşük, gri-mavi
```

### 2.6 Yağış yüzdesi (fallback)
Eğer UDP'de direkt `rainPercentage` yoksa:
```python
WEATHER_TO_RAIN = {
    0: 0,    # Clear
    1: 0,    # Light cloud
    2: 5,    # Overcast
    3: 35,   # Light rain
    4: 70,   # Heavy rain
    5: 95,   # Storm
}
rain_percent = WEATHER_TO_RAIN[weather_code]
```

## 3. Race State Güncelleme Protokolü

**Kopya-üzerine-yaz (CoW) stratejisi:**
```python
class RaceStateStore:
    def __init__(self):
        self._current: dict = {"drivers": {}, "weather": None}
        self._lock = threading.Lock()

    def apply(self, packet):
        # UDP thread'de çalışır
        with self._lock:
            new_state = copy.deepcopy(self._current)
            # ilgili alanları güncelle
            if isinstance(packet, CarStatusPacket):
                for i, car in enumerate(packet.cars):
                    new_state["drivers"][i].ers_percent = ...
            self._current = new_state  # atomic reference swap

    def snapshot(self) -> dict:
        # Render thread'de çalışır
        return self._current  # lock'sız! reference okuması atomic
```

**Not:** Deep copy her pakette pahalı olursa `dataclasses.replace` ile partial update'e döneriz. İlk yaklaşım basit olandır.

## 4. Konfigürasyon Şemaları

### 4.1 `config/layout.json` (4K baseline)
```json
{
  "resolution": [3840, 2160],
  "leaderboard": {
    "origin": [80, 340],
    "size": [480, 1480],
    "row_height": 66,
    "position_col_width": 60,
    "team_bar_width": 8,
    "name_col_x": 78,
    "ers_bar": { "x": 200, "y_offset": 18, "width": 120, "height": 8 },
    "tyre_badge": { "x": 340, "diameter": 34 },
    "tyre_lap_text": { "x": 382, "y_offset": 20 },
    "wear_bar": { "x": 420, "y_offset": 50, "width": 50, "height": 4 }
  },
  "weather_panel": {
    "origin": [80, 260],
    "size": [480, 64]
  },
  "logo_area": {
    "origin": [80, 160],
    "size": [480, 92]
  }
}
```
**Bu değerler placeholder** — araştırma fazında gerçek ölçümlerle değiştirilecek.

### 4.2 `config/theme.json`
```json
{
  "font_family": "Titillium Web",
  "font_fallback": "Arial",
  "background_alpha": 0.82,
  "background_color": "#0A0E14",
  "text_primary": "#FFFFFF",
  "text_secondary": "#B0BEC5",
  "player_highlight": "#FFEB3B",
  "pit_highlight": "#FF9800",
  "ers_colors": ["#7B1FA2", "#3F51B5", "#607D8B"],
  "wear_thresholds": [30, 60, 85],
  "wear_colors": ["#00E676", "#FFEB3B", "#FF9800", "#F44336"]
}
```

### 4.3 `config/teams.json`
```json
{
  "0": { "name": "Mercedes", "color": "#00D2BE", "short": "MER" },
  "1": { "name": "Ferrari", "color": "#DC0000", "short": "FER" },
  "...": "F1 25 takım listesine göre doldurulacak"
}
```

## 5. Hotkey Davranışı

| Tuş | Aksiyon |
|---|---|
| Ctrl+Shift+F1 | Overlay göster/gizle |
| Ctrl+Shift+F2 | Debug mod — bounding box'ları çiz |
| Ctrl+Shift+Q | Uygulamayı kapat |

Kütüphane: `pynput.keyboard.GlobalHotKeys` — ayrı thread, Qt signal üzerinden main thread'e iletiş.

## 6. Loglama

- Default: `INFO` seviyesi, rotating file `logs/overlay.log` (max 5 MB, 3 yedek)
- `--debug` flag → `DEBUG` seviyesi + console
- Paket parse hataları `WARNING`, tek bir paket için stacktrace basılmasın (sürekli aynı hata 60 Hz'de log'u patlatır), **rate-limited** olsun (her hata tipi 10 saniyede 1 kez)

## 7. Performans Hedefleri

| Metrik | Hedef | Nasıl ölçülür |
|---|---|---|
| CPU (overlay process) | <2% (tek çekirdek) | Task Manager, 1 dakikalık yarış |
| RAM | <80 MB | Task Manager |
| F1 25 FPS etkisi | <2 FPS kayıp | Oyun içi FPS counter, overlay açık/kapalı karşılaştırma |
| UDP paket drop | 0 (normal koşulda) | Listener thread counter log |
| Render latency | <5 ms/frame | QPainter timer profiling |

## 8. Bağımlılıklar

`requirements.txt`:
```
PyQt6>=6.6.0
pynput>=1.7.6
```

Hepsi bu. Custom UDP parser yazılırsa ek kütüphane yok. Base olarak bir kütüphane alınırsa (ör. `f1-telemetry-client`), bu listeye eklenecek.

**Python sürümü:** 3.11+ (dataclass match statements + daha iyi struct performance).
