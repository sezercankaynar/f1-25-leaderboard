# 02 — Sistem Mimarisi

## Üst Seviye Diyagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         F1 25 (EA App)                           │
│                                                                   │
│  UDP Telemetri → 127.0.0.1:20777 (60 Hz paketler)                │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   F1Leaderboard.py (Python 3.11+)                │
│                                                                   │
│  ┌─────────────────┐   ┌──────────────────┐   ┌──────────────┐  │
│  │  UDP Listener   │──▶│  Packet Parser   │──▶│  Race State  │  │
│  │  (thread)       │   │  (struct unpack) │   │  (in-memory) │  │
│  └─────────────────┘   └──────────────────┘   └──────┬───────┘  │
│                                                       │           │
│                                                       ▼           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            Qt Main Thread (QApplication)                    │  │
│  │                                                             │  │
│  │   ┌────────────────┐     ┌─────────────────────────────┐   │  │
│  │   │ QTimer 50ms    │────▶│  OverlayWindow (QWidget)    │   │  │
│  │   │ (20 Hz render) │     │  - LeaderboardWidget        │   │  │
│  │   └────────────────┘     │  - WeatherPanelWidget       │   │  │
│  │                          │  - Transparent + StayOnTop  │   │  │
│  │                          └─────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼ (ekranda çizilir)
                   [F1 25 oyun ekranının üstü]
```

## Modüller

### `udp_listener.py`
- **Sorumluluk:** UDP soket aç, paketleri sürekli al, kuyruğa (thread-safe) iter
- **Thread:** Kendi başına `threading.Thread` — render thread'i bloklamaz
- **Buffer:** `queue.Queue(maxsize=256)` — eski paket birikirse drop-oldest politikası
- **Performans hedefi:** <0.5 ms/paket overhead

### `packet_parser.py`
- **Sorumluluk:** Ham bytes → tipli dataclass'lar
- **Yöntem:** Python `struct` modülü + `@dataclass`
- **Paket router:** `packetId` byte'ına göre doğru parser fonksiyonuna yönlendir
- **Dinlenen paketler:** Session(1), LapData(2), Participants(4), CarStatus(7), CarDamage(10)
- **Göz ardı edilen paketler:** Motion(0), CarTelemetry(6), CarSetups(5), Event(3), FinalClassification(8), LobbyInfo(9) — CPU tasarrufu için erken discard
- **Hata politikası:** Parse hatası = paket drop + log warn, çökmez

### `race_state.py`
- **Sorumluluk:** 22 sürücünün birleştirilmiş anlık durumu
- **Veri kaynağı:** Farklı paketlerden gelen parçaları tek `Driver` dataclass'ında birleştir
- **Key data structure:**
```python
@dataclass
class Driver:
    index: int                 # 0..21 (UDP grid pozisyonu)
    position: int              # Canlı sıralama pozisyonu
    name_abbr: str             # "VER", "HAM"
    team_id: int
    team_color: str            # hex
    ers_percent: float         # 0.0..1.0
    tyre_compound: str         # "S"/"M"/"H"/"I"/"W"
    tyre_age_laps: int
    tyre_wear_avg: float       # 0..100, 4 lastiğin ortalaması
    in_pit: bool
    penalty_seconds: int
    is_player: bool
```
- **Thread-safety:** `threading.Lock` veya immutable snapshot pattern (her güncellemede yeni dict)
- **Seçim:** Immutable snapshot (copy-on-write) — render thread'i hiç kilitlenmez, UDP thread yeni snapshot hazırlar

### `weather_state.py`
- Daha küçük bir ayrı dataclass:
```python
@dataclass
class Weather:
    track_temp_c: int
    air_temp_c: int
    rain_percent: int
    weather_code: int          # 0..5, enum
```

### `overlay_window.py`
- **Sorumluluk:** `QWidget` türü şeffaf, framesiz, her zaman üstte pencere
- **Flag'ler:**
  - `Qt.FramelessWindowHint`
  - `Qt.WindowStaysOnTopHint`
  - `Qt.Tool` (taskbar'da görünmesin)
  - `Qt.WindowTransparentForInput`
- **Attribute'lar:**
  - `Qt.WA_TranslucentBackground`
  - `Qt.WA_TransparentForMouseEvents`
- **Geometri:** `layout.json`'dan okunur, 4K koordinatları

### `leaderboard_widget.py`
- Custom `QWidget` — `paintEvent` override
- 22 satırı QPainter ile elle çizer (grid layout kullanmaz, performans için)
- `race_state` snapshot'ını her render'da okur

### `weather_panel_widget.py`
- Yatay mini panel — F1 logosu ile leaderboard arasına çizilir
- 3 ikon + metin: 🌡️ Track, 💨 Air, 🌧️ Rain

### `config_loader.py`
- `config/layout.json` — piksel koordinatları
- `config/theme.json` — renkler, fontlar, bar stilleri
- `config/tire_compounds.json` — UDP enum → rozet mapping

### `app.py` (entry point)
- `QApplication` başlat
- UDP thread'i başlat
- Overlay penceresini oluştur ve göster
- Global hotkey dinleyici (`pynput` kütüphanesi) — Ctrl+Shift+F1 toggle
- Graceful shutdown (Ctrl+C veya sistem tepsisi sağ tık → exit)

## Thread Modeli

| Thread | Rol | Engellenme riski | Not |
|---|---|---|---|
| Main (Qt) | UI render | QTimer içinde sadece snapshot kopyala ve çiz | Bloklanırsa overlay donar |
| UDP Listener | Soket dinle | `socket.recvfrom` bloklanır (ideal) | Daemon thread, app kapanınca ölür |
| State Updater | Parse + snapshot üret | UDP thread içinde senkron çalışabilir | Ayrı thread'e gerek yok, parse ucuz |
| Hotkey Listener | pynput callback | Kendi thread'i | Qt ile signal üzerinden konuşsun |

**Qt thread-safety kuralı:** UI'a ne olursa olsun **main thread** dışından dokunulmaz. UDP thread'ten overlay'e veri geçişi **pyqtSignal** ile değil, shared immutable dict ile — her QTimer tick'inde main thread son snapshot'ı okur.

## Veri Akışı (Tek Bir Frame)

```
1. UDP Listener thread:
   ├── socket.recvfrom() → raw bytes
   ├── packet_parser.parse(raw_bytes) → dataclass
   ├── race_state.apply(parsed_packet) → yeni snapshot dict
   └── shared_state["latest"] = snapshot (atomic dict swap)

2. Qt Main thread (QTimer her 50 ms):
   ├── snapshot = shared_state["latest"]
   ├── leaderboard_widget.update_data(snapshot)
   ├── weather_panel.update_data(snapshot.weather)
   └── self.update()  # Qt paintEvent tetikler

3. paintEvent:
   └── QPainter ile doğrudan çizim (widget ağacı yok)
```

**Neden QTimer, QThread değil?** UDP thread zaten async, render için fixed rate yeterli. 60 Hz paket alıp 20 Hz render etmek CPU açısından ideal — oyundaki FPS düşüşü minimum.

## Render Rate Kararı
- UDP gelen: 60 Hz (Car Telemetry) — biz bunu dinlemiyoruz zaten
- UDP gelen: 10 Hz (Car Status, Car Damage)
- Render: **20 Hz** (50 ms tick)
- Gerekçe: Göz 20 Hz'in altındaki güncellemeleri yavaş hisseder, üstü kaynak israfı. Hava paneli için 2 Hz yeterli ama birleşik render loop'u basit tutuyoruz.

## Konfigürasyon Dosyaları

```
.config/
├── layout.json          # Piksel koordinatları (4K baseline)
├── theme.json           # Renkler, fontlar, bar stilleri
├── tire_compounds.json  # UDP enum → rozet map
└── teams.json           # teamId → ad + renk
```

**Neden JSON, Python config değil?** Kullanıcı (sen) kolay düzenleyebil diye. 1080p/1440p preset'leri sonradan `layout_1080p.json` gibi eklenebilir.

## Güncelleme/Dağıtım Stratejisi

Kişisel kullanım olduğu için:
- Tek klasör: `F1Leaderboard/`
- Python embedded distribution (~15 MB) paketle → kullanıcı Python yüklemesin
- `run.bat` → `python app.py`
- Gerekirse PyInstaller ile tek `.exe` — M6 fazında karar
