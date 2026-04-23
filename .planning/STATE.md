# Oturum Handoff — Mevcut Durum

> Bu doküman bir önceki oturum context doluyken yazıldı. Yeni oturum buradan devam eder.

## Tamamlanan Fazlar

### ✅ Faz 0 — Proje İskeleti
- `requirements.txt` (PyQt6, pynput), `.gitignore`, `README.md`
- `f1_leaderboard/` paket + 7 modül stub
- `config/` — `layout.json` (4K baseline), `theme.json`, `teams.json` (2025 grid), `tire_compounds.json`
- **DoD:** Python syntax ✓, JSON valid ✓. Qt boş pencere canlı test edilmedi ama `app.py` sonradan genişletildi, konu kapandı.

### ✅ Faz 1 — UDP Bağlantısı
- `f1_leaderboard/udp_listener.py` — daemon thread, drop-oldest kuyruk
- `f1_leaderboard/packet_parser.py` — header parser + 14 paket ID tablosu
- `dev_tools/dump_udp.py` — binary capture aracı, `[ts:f64][len:u16][bytes]`
- `dev_tools/replay_udp.py` — speed parametreli replay
- **DoD:** 60 saniyede 13,469 paket, 0 drop. `packet_format=2025`, `game_year=25` doğrulandı.

### ✅ Faz 2 — Paket Gövde Parserleri + Race State
Spec kaynağı: https://github.com/MacManley/f1-25-udp README struct'ları
Capture boyutlarıyla doğrulandı (pid=1 size=753, pid=2 size=1285, pid=4 size=1284, pid=7 size=1239, pid=10 size=1041).

- `packet_parser.py` genişletildi:
  - `parse_session` — weather/trackTemp/airTemp/totalLaps (@0-3)
  - `parse_lap_data` — carPosition@32, currentLapNum@33, pitStatus@34, penalties@38 (per-car 57 byte)
  - `parse_participants` — teamId@3, name@7-38 (per-car 57 byte, F1 25'te 57 — F1 24 ile fark)
  - `parse_car_status` — visual/actualTyreCompound@25-26, tyresAgeLaps@27, ersStoreEnergy@37 (per-car 55 byte, ERS_MAX=4,000,000 J)
  - `parse_car_damage` — tyresWear[4]@0 (per-car 46 byte)
  - Router `parse(data)` — 5 ilgilenilen paketi dispatch eder, diğerlerini skip
- `race_state.py` — `Driver`, `Weather`, `Snapshot`, `RaceStateStore` (lock + reference-swap CoW)
- `dev_tools/inspect_capture.py` — capture → snapshot dökümü

**Doğrulama (Grand Prix 5 lap, 20 araç, Monaco/kısa pist):**
- 2025 grid isimleri doğru (VER, HAM, LEC, RUS, ANTONELLI, BEARMAN, HADJAR, LAWSON, COLAPINTO, BORTOLETO...)
- Takım ID'leri 0-9, her takımda 2 sürücü ✓
- ERS %51-100 dağılmış (AI simülasyonu gerçekçi — R3 riski bertaraf)
- Tyre wear 1.9-2.5% (2 tur sonrası mantıklı)

### ✅ Faz 3 — Minimal Görsel Overlay (CANLI TEST ONAYLANDI 2026-04-21)
- `leaderboard_widget.py` — QPainter ile pozisyon + 3-harf kod, player highlight, waiting state
- `overlay_window.py` — FramelessWindowHint + WindowStaysOnTopHint + Tool + WindowTransparentForInput + WA_TranslucentBackground + WA_TransparentForMouseEvents + WA_ShowWithoutActivating; primary screen origin'ine setGeometry, çoklu monitör güvenli
- `app.py` — config yükleme + UdpListener + pump thread + RaceStateStore + QTimer 50ms render + graceful shutdown + **runtime scale layer** + periyodik debug tick (recv/parsed/by_pid/drivers)

**Canlı test doğrulaması (Windowed Fullscreen, 1080p, 3. monitör primary):**
- Ekran görüntüsünde 20 sıra düzgün görünüyor: LEC 1, TSU 2, NOR 3, RUS 4, SAI 5 ... HUL 20
- Player (HUL) sarı highlight ✓
- Click-through ✓
- Pozisyonlar canlı değişiyor ✓
- UDP sağlık: `recv=4283 parsed=1431 by_pid={1:57, 4:6, 10:282, 2:543, 7:543} | pos>0=20 named=20`
- Render overhead gözle belirgin değil (20 Hz @ 50ms interval)

**Bu fazda öğrendiklerimiz (kritik sürprizler):**

1. **F1 25 Windowed (Fullscreen) modu ana monitörün çözünürlüğüne kilitleniyor** — sadece 1920×1080 seçeneği sunuyor. 4K oyun için 4K monitörün **primary** olması gerek. 3 monitörlü kurulumda 3. monitörü primary yapmak zorunda kaldık.
2. **Kullanıcının ortamında 4K bile primary seçilse oyun yine 1080p veriyor** — neden belirsiz (kablo bandwidth, driver, oyun cache). 1080p ile yaşamayı kabul ettik.
3. **4K baseline layout'u runtime'da scale ediyoruz** — `app.py::_scale_layout()`: primary screen boyutunu alır, `layout.resolution`'a göre scale hesaplar, tüm piksel değerlerini (origin, size, fontlar dahil) recursive çarpar. Layout.json 4K baseline olarak kalır, 1080p'de 0.5× uygulanır. **Font boyutları** `layout.leaderboard.font_pos_size` / `font_name_size` olarak layout'a eklendi (önceden hardcoded).
4. **`screen_origin` ekledik** — primary screen (0,0) olmayabilir (çoklu monitör virtual desktop). OverlayWindow `setGeometry(ox, oy, w, h)` ile çalışıyor.
5. **Debug timer kalıcı** — `app.py` içinde `_debug_tick` 1sn'de bir `recv/parsed/by_pid/drivers` loglar. Faz 4'te de UDP sağlığı için faydalı, production (Faz 6) öncesi kapat.
6. **`hardware_settings_config.xml` sıfırlama telemetry ayarını da sıfırlıyor** — test öncesi UDP Format = 2025 ve UDP Telemetry = On yeniden ayarlanması gerekti.
7. **Windows DPI Scaling %200 aktif** — Ekran görüntüleri fiziksel **3840×2160** (4K) yakalanıyor, Qt logical **1920×1080** rapor ediyor. Overlay logical 1080p koordinatta çizilir, Windows compositor fiziksel 4K'ya upscale eder. **Bu yüzden F1 25 "4K seçtirmiyor" gözükse de ekran gerçekte 4K render ediyor** — oyun UI'si upscale'den keskin geliyor. Bu bilgi değişti: layout.json **4K baseline olarak kalabilir**, piksel ölçümleri doğrudan ekran görüntüsü 4K koordinatlarından alınır, runtime `_scale_layout()` 0.5× ile logical 1080p'ye çevirir, Windows %200 DPI ile fiziksel 4K'ya geri döner.

## Ekran Görüntüsü Piksel Ölçümleri (with_hud.png / without_hud.png, 3840×2160)

**Oyun leaderboard bölgesi** (with_hud.png):
- Bounding box: yaklaşık `(0, 170)` → `(560, 1790)` (4K piksel)
- 20 satır, satır yüksekliği ~81px
- Bu bölge bizim overlay'in hizalanması gereken canvas

**Oyunun açık kalan HUD öğeleri** (without_hud.png):
- `F1 RACE` başlığı + `LAP N/M` banner: `(0, 0)` → `(450, 170)` — overlay başlangıcı bunun hemen altına
- Sol alt minimap: `(0, 1780)` → `(420, 2080)` — overlay bitişi bunun üstünde olmalı
- Sağ üst pozisyon göstergesi: `(3070, 0)` → `(3840, 130)` — çakışma riski yok
- Sağ alt panel (overtake/clutch): oyun tarafı, değişmez

**Faz 4 için önerilen layout.json güncellemeleri** (detaylar plan-phase aşamasında fine-tune):
| Alan | Mevcut | Önerilen (4K) |
|---|---|---|
| `leaderboard.origin` | `[80, 340]` | `[20, 190]` |
| `leaderboard.size` | `[480, 1480]` | `[560, 1600]` |
| `leaderboard.row_height` | `66` | `80` |

## 🔜 Sıradaki Adım — Faz 4 (Sıralama Tablosu)

### ⚠️ 2026-04-21 Kapsam Revizyonu
Kullanıcı `example.png` hedef görselini paylaştı. İlk plandaki F4 (ERS barı + aşınma barı) hedefle uyumsuzdu. Kapsam yeniden çizildi:
- **F4'ten çıkarıldı**: ERS barı, aşınma barı, pit/penalti etiketi, üst tur sayacı başlığı
- **F4'e eklendi**: Takım logosu (PNG asset), sektör gelişimi mini-barları, önündeki ile zaman farkı
- **F5'e taşındı**: Başlık bandı (F1 logo + session + lap N/M) + hava paneli

### Faz 4 Kapsamı — Sıralama Tablosu (kullanıcı onayı var)
Soldan sağa kolonlar:
1. Pozisyon (lider sarı kutu)
2. Takım renk barı (teams.json'dan, şu an bug'lı — hepsi aynı renk)
3. Takım logosu (PNG, yeni asset)
4. Sürücü 3-harf kodu
5. Sektör gelişimi (3 mini-bar: mevcut mor, geçilen yeşil, gelecek gri)
6. Önündeki ile gap (`+0.312` / `LEADER` / `+1 LAP`)
7. Lastik compound rozeti + ömür (`L12`)

Hedef görseldeki 2 yuvarlak nokta (sağda mavi olan) çizilmeyecek.

### Asset İhtiyacı — Faz 4 Başında
10 takım logosu PNG (kullanıcı: "sen sağla"):
- Red Bull, Ferrari, Mercedes, McLaren, Aston Martin, Alpine, Williams, Racing Bulls, Kick Sauber, Haas
- Şeffaf arka plan, ~64×64 px, <20 KB
- Hedef konum: `config/assets/teams/{teamId}.png`

### Faz 4 Öncesi Ön Koşullar (kullanıcı tarafı)
1. **Oyunun kendi leaderboard HUD'ını kapat** — F1 25 Pause → HUD → Leaderboard: **Off**. (A+C kombinasyonu, kullanıcı 2026-04-21 seçti.) Overlay'in tek pozisyon kaynağı olması görsel karmaşayı azaltır.
2. **Piksel ölçümü** — `.planning/01-research.md` checklist'indeki HUD piksel ölçümü henüz yapılmadı. F4 layout sayılarını placeholder yerine gerçek değerlere bağlamak için:
   - 1080p oyun ekran görüntüsü al (racing hattında, leaderboard görünür)
   - Her satırda: pos genişliği, team bar genişliği, ERS bar koordinatı, lastik rozet çapı, aşınma bar offset
   - `.planning/01-research.md` içindeki ilgili bölüme yaz, veya STATE.md'ye direkt ekle
3. **Team renk paleti doğrulama** — `config/teams.json` 2025 renkleri ama HSB değerleri kalibre edilmedi. Ölçüm sırasında ekran görüntüsünden renkleri eye-dropper ile çıkar.

### Faz 4 Plan Dosyası
`.planning/05-phases.md` içinde F4 genel hatları var ama detay yok. `/gsd:plan-phase 4` ile detay plan oluşturulacak, sonra `/gsd:execute-phase 4`.

## Sıradaki Fazlar (plan)

- **F5** — Başlık bandı + hava paneli: F1 logosu + session type (`P1`..`YARIŞ`) + `LAP N/M` banner, altında 🌡 track / 💨 air / 🌧 rain paneli.
- **F6** — Cila: hotkey (Ctrl+Shift+F1 toggle), tray icon, PyInstaller build, README genişletme, debug_timer kaldırma, opsiyonel F1 purple/green sektör konvansiyonu (SessionHistory paketi gerekir).

## Açık Sorular / Bilinmeyenler

1. **`rainPercentage` gerçek bir UDP alanı mı?** Şu an weather enum'dan fallback kullanıyoruz (`_WEATHER_TO_RAIN` map). F1 25 spec PDF'inde (EA Forums link 01-research.md'de) doğrulanacak. Fallback'in değeri acceptable — ama gerçek alanı bağlamak daha doğru olur, dinamik hava olan yarışta daha hassas.
2. **~~Yerel HUD'un gerçek 4K piksel koordinatları~~** → 4K mümkün değil, kurulum 1080p kalacak. F4 öncesi piksel ölçümü **1080p ekran görüntüsü** üzerinden yapılacak. Baseline layout.json yine 4K'da kalabilir (runtime scale), ama ölçümleri 1080p'de alıp 2× ile base'e çevirmek gerek. Ya da layout.json'ı 1080p base'e döndür — ileride biri 4K'ya geçince scale yine çalışır (1.0×).
3. **F1 logosu alanının gerçek bounding box'ı.** Hava paneli yerleşimi için F5 öncesinde gerek.
4. **~~Fullscreen exclusive davranışı~~** → Windowed (Fullscreen) ile çalışıyor, exclusive DXGI test edilmedi, gerek de yok.
5. **F1 25 neden 4K seçtirmiyor** — ana monitör 4K yapılmasına rağmen oyun 1080p'de kalıyor. Kablo mu, driver mi, hardwaresettings cache mi? Kullanıcı 1080p ile yaşamayı kabul etti — araştırma askıya alındı.

## Faz 3 Kapanışında Kod Değişiklikleri (2026-04-21 özet)

- `config/layout.json` — `leaderboard.font_pos_size` (22), `leaderboard.font_name_size` (20) eklendi
- `f1_leaderboard/app.py` — `_scale_layout()` helper, `_pump_loop` stats dict, `_debug_tick` QTimer (1sn)
- `f1_leaderboard/overlay_window.py` — `move(0,0)` → `setGeometry(ox, oy, w, h)`, çoklu monitör için `screen_origin` okur
- `f1_leaderboard/leaderboard_widget.py` — fontları layout'tan okur, boş drivers listesinde "waiting for UDP…" fallback mesajı (önceki `_snapshot is None` kontrolü hiç çalışmıyordu çünkü store hep Snapshot döndürüyor)

## Referans Kaynaklar (bu oturumda kullanıldı)

- F1 25 UDP Spec (resmi): https://forums.ea.com/t5/s/tghpe58374/attachments/tghpe58374/f1-games-game-info-hub-en/61/4/Data%20Output%20from%20F1%2025%20v3.pdf
- Topluluk parser: https://github.com/MacManley/f1-25-udp
- Capture örneği: `captures/race_01.bin` (time trial, 60s, 13,469 paket)
- Capture örneği: `captures/career_01.bin` (Grand Prix 5 lap, 90s, 23,789 paket) — F2 doğrulaması bu dosya üzerinde

## Kullanıcı Tercihleri (Discuss fazından)

- Yaklaşım: **Harici overlay** (UDP telemetri), yerel HUD'un **üstüne bindir**
- Tech: **Python 3.11+ + PyQt6** (50-100 MB RAM kabul edilebilir)
- Platform: **EA App** (PC), **4K** monitör
- Hedef kitle: kişisel + birkaç arkadaş (installer gerekmez)
- MVP veri seti: pozisyon + sürücü + takım rengi + ERS bar + lastik (compound + tur) + aşınma yüzdesi + hava paneli (track/air temp + rain%)
- Gap zamanı ve DRS MVP dışı

## Proje Yapısı (mevcut)

```
f1 25 leaderboard patch/
├── .planning/
│   ├── ROADMAP.md
│   ├── 01-research.md ... 07-risks.md
│   └── STATE.md                 ← bu dosya
├── f1_leaderboard/
│   ├── __init__.py
│   ├── app.py                   ← entry point
│   ├── udp_listener.py          ← F1 ✓
│   ├── packet_parser.py         ← F2 ✓
│   ├── race_state.py            ← F2 ✓
│   ├── overlay_window.py        ← F3 ✓ (çoklu monitör, setGeometry)
│   ├── leaderboard_widget.py    ← F3 ✓ (font layout'tan, waiting fallback)
│   ├── weather_panel_widget.py  ← F5 stub
│   └── config_loader.py         ← kullanılmıyor (app.py doğrudan JSON okuyor)
├── config/
│   ├── layout.json              ← 4K baseline, placeholder
│   ├── theme.json
│   ├── teams.json               ← 2025 renkleri, doğrulanacak
│   └── tire_compounds.json
├── dev_tools/
│   ├── dump_udp.py              ← capture
│   ├── replay_udp.py            ← replay
│   └── inspect_capture.py       ← snapshot dump
├── captures/                    ← git'e girmez
├── requirements.txt
├── .gitignore
└── README.md
```
