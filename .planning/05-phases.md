# 05 — İmplementasyon Fazları

Her faz bir `Definition of Done` (DoD) ile biter. DoD karşılanmadan sonraki faza geçilmez. "Geçici olarak atlarız, sonra döneriz" **yasak** — bir kez bırakılan iş iki misli zor geri döner.

## Faz 0 — Proje İskelesi (1-2 saat)

### Amaç
Geliştirme ortamını kurmak, proje dosya yapısını oluşturmak.

### Görevler
- [ ] `f1_leaderboard/` Python paket klasörü oluştur
- [ ] `requirements.txt` yaz (PyQt6, pynput)
- [ ] `.venv` oluştur, bağımlılıkları yükle
- [ ] `README.md` skeleton (kurulum, kullanım)
- [ ] `.gitignore` — `__pycache__/`, `.venv/`, `logs/`
- [ ] Boş modül dosyalarını oluştur: `udp_listener.py`, `packet_parser.py`, `race_state.py`, `overlay_window.py`, `app.py`
- [ ] `config/` klasörü + boş JSON'lar

### DoD
- `python -m f1_leaderboard.app` komutu çalışır (boş Qt penceresi açılır, hata vermez)
- `pip freeze` çıktısı `requirements.txt` ile eşleşir

---

## Faz 1 — UDP Bağlantısı (4-6 saat)

### Amaç
F1 25'in UDP telemetri akışını dinle, ham paketleri al, `packetId`'ye göre logla.

### Görevler
- [ ] UDP spec araştırması tamamla (01-research.md checklist)
- [ ] `udp_listener.py` — bağımsız thread, paketleri `queue.Queue`'ya koy
- [ ] `packet_parser.py` — sadece `PacketHeader` parse et (geri kalan paket byte'larını tut)
- [ ] Router: her paket için `packetId` + boyut logla
- [ ] `dev_tools/dump_udp.py` — yakalanan paketleri `.pcap` benzeri binary dosyaya kaydet (replay için)

### Test
Kariyer modunda 30 saniyelik bir yarış süresince:
- En az 5 farklı paket ID'si gözlemle (1, 2, 4, 7, 10 asgari)
- Paket boyutları spec'teki değerlerle eşleşsin
- 0 exception/crash

### DoD
- Log dosyası: `logs/udp_capture.log` — son 30 saniyede gelen paket sayıları per `packetId`
- `dump_udp.py` → `captures/race_01.bin` (replay için kullanılacak)
- Hiçbir paket parse edilmemiş olsa bile listener temiz kapanır

---

## Faz 2 — Paket Parser + Race State (3-4 saat)

### Amaç
İhtiyaç duyulan 5 paketi tipli dataclass'lara parse et, `RaceStateStore`'a yaz.

### Görevler
- [ ] `packet_parser.py` — 5 paket için `parse_*` fonksiyonları
- [ ] `race_state.py` — `Driver`, `Weather`, `RaceStateStore` dataclass'ları
- [ ] `race_state.apply()` — gelen parsed paketi state'e merge
- [ ] Takım kodu/renk/lastik compound map'lerini `config/` altına koy
- [ ] `dev_tools/replay_udp.py` — `captures/*.bin` dosyasını 60 Hz'de UDP loopback'e replay etsin

### Test
- `captures/race_01.bin` replay'inde state consistency — 10 saniye sonra:
  - `snapshot["drivers"]` 22 eleman
  - Her driver'ın `position`, `ers_percent`, `tyre_compound` alanı dolu
  - `snapshot["weather"]` dolu
- Unit test: her paket tipi için örnek byte dizisi → expected dataclass

### DoD
- `pytest tests/test_parser.py` geçer
- Manual replay çalıştırıldığında konsola her 1 saniyede bir 22 sürücü özeti basılır
- `race_state.snapshot()` hiçbir zaman `None` döndürmez (boş state ile başlar)

---

## Faz 3 — Minimal Görsel Overlay (4-6 saat)

### Amaç
Şeffaf, framesiz, üstte kalan bir pencere aç, sadece **pozisyon + sürücü adı** listesini çiz.

### Görevler
- [ ] `overlay_window.py` — transparan QWidget, doğru flag'ler
- [ ] QTimer 50 ms, `race_state.snapshot()` oku
- [ ] `leaderboard_widget.py` — sadece 22 satır, pozisyon + 3-harf kod
- [ ] `config/layout.json` — placeholder değerler
- [ ] Click-through davranışını doğrula (Notepad'e overlay üzerinden tıklayabilmelisin)

### Test
- F1 25 yarışta. Overlay açık. 22 sürücü listesinde pozisyonlar canlı değişiyor.
- Alt-Tab sonrası pozisyon korunuyor.

### DoD
- Borderless modda F1 25 üstünde overlay görünür
- 20 Hz render'da FPS düşüşü ölçülmez (±1 FPS)
- Overlay click-through — mouse oyuna geçer

---

## Faz 4 — Sıralama Tablosu (8-12 saat)

**2026-04-21 revizyonu:** Kapsam `example.png` hedef görseline göre yeniden çizildi. ERS barı + aşınma barı çıkarıldı, takım logosu + sektör göstergesi + gap kolonu + başlangıç sürümü lastik (kompound+ömür) girdi. Üst başlık + hava paneli **F5'e** taşındı.

### Amaç
Hedef görsel (`example.png`) ile pikselce oturan sıralama tablosu. **Sadece tablo** — başlık bandı ve hava paneli yok.

### Kolon dizisi (soldan sağa)
1. Pozisyon (lider sarı kutu)
2. Takım renk barı (dikey)
3. Takım logosu (PNG)
4. Sürücü 3-harf kodu
5. Sektör gelişimi (3 mini-bar)
6. Önündeki ile zaman farkı (`+0.312`)
7. Lastik (compound rozeti + `L##` ömür)

### Görevler

**Asset hazırlığı:**
- [ ] Takım logoları indir — 10 takım × 1 PNG (şeffaf, ~64×64): Red Bull, Ferrari, Mercedes, McLaren, Aston Martin, Alpine, Williams, Racing Bulls, Kick Sauber, Haas
- [ ] `config/assets/teams/{team_id}.png` olarak yerleştir (teamId sayı ile eşleşsin)
- [ ] Dosya boyutu < 20 KB/logo — optimize et
- [ ] `config/teams.json`'a `logo_path` alanı ekle

**Veri bağlantıları (packet_parser genişletme):**
- [ ] `LapData.sector` (u8, offset bul) — şu an hangi sektörde
- [ ] `LapData.deltaToCarInFront*` — ms cinsi gap, int32 ya da benzeri
- [ ] `CarStatus.tyresAgeLaps` parse (zaten Faz 2'de var, doğrula)
- [ ] Yeni alanları `Driver` dataclass'ına ekle: `current_sector`, `delta_to_ahead_ms`
- [ ] Lider için gap değeri `None` olmalı, widget `LEADER` gösterir
- [ ] Lap-down durumu: `LapData.currentLapNum` farkı ≥1 ise `+N LAP` göster

**Widget render (`leaderboard_widget.py`):**
- [ ] Satır yüksekliği 80 px (4K), kolon offset'leri `04-ui-design.md` tablosundan
- [ ] Pozisyon: lider sarı dolgulu kutu + siyah yazı, diğerleri transparan + beyaz
- [ ] Takım renk barı — `teams.json[teamId].color` (şu an bozuk, eşleşmeyi düzelt)
- [ ] Takım logosu — QPixmap cache (uygulama başında 1 kez yükle, satır başına çizme sırasında drawPixmap)
- [ ] Sürücü 3-harf — mevcut render, x offset güncellenecek
- [ ] Sektör mini-barları — 3 dikey dikdörtgen, geçilen mor/yeşil, gelecek gri
- [ ] Gap metni — format fonksiyonu (`format_gap(delta_ms, laps_behind)`)
- [ ] Lastik rozeti — 34 px daire + compound harfi, `tire_compounds.json` rengi
- [ ] `L` + tur sayısı — rozetin sağında

**Layout:**
- [ ] `config/layout.json` güncelle — yeni row_height 80, kolon genişlikleri, leaderboard bounding box `(20, 190)` → `(580, 1790)` (STATE.md ölçümlerinden)

**Doğrulama:**
- [ ] Oyuncu satırı sarı vurgu (mevcut, koru)
- [ ] Takım renk barı gerçekten 10 farklı renk gösteriyor (şu an bug)

### Test
- Gerçek kariyer yarışında (5 lap yeterli):
  - 10 takım renk barı net farklı
  - 10 takım logosu görünür (bulanık değil)
  - Gap değeri canlı güncelleniyor, lider için `LEADER`
  - Sektör barları tur içinde ilerliyor, turun başında sıfırlanıyor
  - Lastik compound + ömür doğru (pit stop sonrası L1'e düşüyor)

### DoD
- 20 sürücünün hepsi hedef görseldeki dizilimle render ediliyor
- Overlay + oyun aynı anda çalışırken FPS farkı <2
- Screenshot: `docs/screenshots/f4_final.png` — kullanıcı onayı

---

## Faz 5 — Başlık Bandı ve Hava Paneli (3-4 saat)

**2026-04-21 revizyonu:** Eski F5 sadece hava paneliydi. Hedef görselde başlık bandı (F1 logo + session type + lap N/M) ve hava paneli **beraber** üst bölgede yer alıyor — ikisini tek fazda birleştirdim.

### Amaç
Sıralama tablosunun üstünde 2 satırlık header: logo+session+tur, onun altında pist/hava/yağış paneli.

### Görevler
- [ ] F1 logosu asset (şeffaf PNG, `config/assets/f1_logo.png`)
- [ ] Session type string map — `Session.sessionType` → `P1`/`P2`/`P3`/`Q1`/`Q2`/`Q3`/`SQ1`/`SQ2`/`SQ3`/`SPRINT`/`YARIŞ`
- [ ] `header_widget.py` — F1 logo + dinamik `{SESSION} {lap}/{total}` metni
- [ ] `weather_panel_widget.py` bitir — 3 kolon: 🌡 pist / 💨 hava / 🌧 yağış (ikon SVG ya da emoji kararı bu fazda)
- [ ] Session paketinden `trackTemperature`, `airTemperature`, `weather` veya `rainPercentage` bağla
- [ ] `layout.json`'a `header` + `weather_panel` origin/size
- [ ] Pist ısısı >45°C kırmızı vurgu

### Test
- Session tipi değişince başlık güncelleniyor (practice → qualy → race)
- Yağmurlu yarışta rain% artıyor
- Başlık + hava + leaderboard üçü hizalı, taşma yok

### DoD
- Başlık + hava paneli + leaderboard tek bütün görünüyor
- 20 dakikalık yarış boyunca crash yok
- Screenshot: `docs/screenshots/f5_final.png`

---

## Faz 6 — Cila ve Yaşam Kalitesi (3-5 saat)

### Amaç
Kullanılabilir, dağıtılabilir bir sürüm.

### Görevler
- [ ] Hotkey sistemi — Ctrl+Shift+F1 toggle
- [ ] Sistem tepsisi ikonu — sağ tık menüsü (Exit, Toggle Debug, Open Config)
- [ ] `--debug` CLI flag — bounding box overlay
- [ ] Loglama rotation ayarları finalize
- [ ] `build.bat` — PyInstaller ile tek `.exe` (opsiyonel)
- [ ] README'de kurulum + UDP ayarları + ekran görüntüleri
- [ ] F1 25 ayarları için screenshot rehberi

### Test
- Temiz bir Windows kullanıcı profilinde ZIP'i çıkar, `run.bat` ile çalıştır — ek kurulum olmadan çalışsın
- Hotkey overlay'i göster/gizle
- Log dosyası 5 MB'da rotate ediyor

### DoD
- `F1Leaderboard_v0.1.zip` — tek dosya, açıp çalıştırılabilir
- README: en az 3 ekran görüntüsü, 5 dakika okuma süresi
- Temiz bir yarıştan sonra crash yok, log'da error yok

---

## Faz Bağımlılıkları

```
F0 ──▶ F1 ──▶ F2 ──▶ F3 ──▶ F4 ──▶ F6
                      │         ▲
                      └──▶ F5 ──┘
```

F4 ve F5 F3'ten sonra paralel olabilir ama tek kişilik projede sıralı — F4 daha büyük, önce o.

## Paralelleştirme Notu
Kişisel proje olduğu için paralellik yok. Ama M4'ün içinde UI detayları (lastik rozeti, ERS bar, aşınma bar) alt-task olarak ayrı günlere yayılabilir.

## Süre Toplamı (Tekrar)
| Faz | Alt limit | Üst limit |
|---|---|---|
| F0 | 1 | 2 |
| F1 | 4 | 6 |
| F2 | 3 | 4 |
| F3 | 4 | 6 |
| F4 | 8 | 12 |
| F5 | 2 | 3 |
| F6 | 3 | 5 |
| **Toplam** | **25 saat** | **38 saat** |

Haftada 4-5 saat çalışılırsa 6-8 hafta. Yoğun hafta sonu çalışması ile 2 hafta.
