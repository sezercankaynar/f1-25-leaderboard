# 06 — Test Stratejisi

## Felsefe
Bu bir canlı oyun overlay'i. Her değişikliği test için 30-40 dakikalık yarış başlatmak sürdürülebilir değil. Bu yüzden **UDP kayıt + replay altyapısı en önemli test kaldıracımız**. Bir kez iyi kayıt alırsan, kodun %80'ini oyuna dokunmadan test edersin.

## Test Piramidi

```
                     ┌─────────────┐
                     │ Canlı yarış │      (nadiren, manuel)
                     │   testi     │
                     └─────────────┘
                ┌─────────────────────┐
                │    Replay testi     │   (orta, yarı-otomatik)
                │  (kaydedilmiş UDP)  │
                └─────────────────────┘
         ┌────────────────────────────────┐
         │        Unit testler             │  (sık, otomatik)
         │  (parser, state, helpers)       │
         └────────────────────────────────┘
```

## 1. Unit Testler (pytest)

### 1.1 Kapsam
- `packet_parser`: her paket tipi için örnek byte dizisi → expected dataclass
- `race_state.apply`: paket merge kuralları
- `tire_compounds`: enum → rozet map
- `helpers`: `wear_color()`, `ers_color()`, `derive_abbr()`
- Edge case: bozuk paket (kısa buffer, yanlış version) — hata log, crash yok

### 1.2 Test veri seti
- `tests/fixtures/session_packet.bin` — gerçek yarıştan alınmış bir Session paketi
- Her paket için benzer fixture
- `tests/fixtures/race_30s.bin` — 30 saniyelik tam akış

### 1.3 Çalıştırma
```bash
pytest tests/ -v
```

### 1.4 DoD
- En az 20 test case
- `packet_parser` coverage %90+
- CI yok (kişisel proje), sadece `pytest` çalışması geçsin

## 2. Replay Testi (Yarı-otomatik)

### 2.1 UDP Capture
**Script:** `dev_tools/dump_udp.py`
- Gerçek yarışta UDP paketlerini dinle
- Her pakete timestamp ekle
- `.bin` dosyasına yaz (basit binary format: `[timestamp:float64][len:uint16][bytes]`)

### 2.2 UDP Replay
**Script:** `dev_tools/replay_udp.py`
- Capture dosyasını oku
- Orijinal zaman aralıklarını koruyarak 127.0.0.1:20777'e gönder
- `--speed 2.0` ile hızlandırılabilsin

### 2.3 Kullanım
```bash
# 1. Test senaryoları için capture'lar hazırla (tek sefer)
python dev_tools/dump_udp.py --output captures/dry_race.bin --duration 600
python dev_tools/dump_udp.py --output captures/wet_race.bin --duration 600
python dev_tools/dump_udp.py --output captures/pit_stop.bin --duration 120

# 2. Kod değişikliklerini replay ile dene
python dev_tools/replay_udp.py captures/wet_race.bin --speed 3.0
# Başka terminalde: python -m f1_leaderboard.app
```

### 2.4 Test Senaryoları (Capture Listesi)
- [ ] `dry_race.bin` — 10 dakikalık kuru yarış, normal koşullar
- [ ] `wet_race.bin` — yağmurlu yarış, Inter→Wet geçişi
- [ ] `pit_stop.bin` — pit stop sekansı (Soft→Medium değişim, tyresAgeLaps reset)
- [ ] `qualifying.bin` — sıralama turu (pit durumu yoğun)
- [ ] `safety_car.bin` — SC / VSC durumu

Bu capture'lar `captures/` klasöründe, git'te yok (büyük dosyalar, `.gitignore`).

## 3. Görsel Regresyon Testi (Semi-manual)

### 3.1 Screenshot compare
- Her release öncesi: replay çalıştır, belirli zaman noktalarında overlay ekran görüntüsü al
- Önceki sürümle piksel diff (ImageMagick `compare`) — kabul edilebilir delta %1

### 3.2 Checklist — gerçek yarışta gözle
Her görsel değişiklik sonrası:
- [ ] 22 satır hepsi görünüyor, kırpılma yok
- [ ] Oyuncu satırı sarı vurgulu
- [ ] Lastik rozeti renkleri doğru (S=kırmızı, M=sarı, H=beyaz, I=yeşil, W=mavi)
- [ ] ERS bar'ları %0 ve %100'de doğru uçlar
- [ ] Aşınma bar'ı %85+ kırmızı
- [ ] Pit'teki araç turuncu
- [ ] Takım rengi şeritleri doğru renkte
- [ ] Hava paneli 3 veriyi gösteriyor
- [ ] Leaderboard ile yerel HUD pikselce hizalı (±2 px)

## 4. Performans Testi

### 4.1 FPS impact
- Oyun ayarlarında FPS counter aç
- 30 saniye lap, overlay kapalı → ortalama FPS_off
- Aynı 30 saniye, overlay açık → ortalama FPS_on
- **Hedef:** `FPS_off - FPS_on < 2`

### 4.2 Kaynak kullanımı
- Task Manager → overlay process
- 10 dakikalık yarış boyunca: CPU <2%, RAM <80 MB
- RAM leak testi: 30 dakika → RAM %10'dan fazla artmıyor

### 4.3 Paket drop
- Listener thread'de counter: `packets_received`, `packets_dropped`
- Normal koşulda drop = 0 olmalı

## 5. Canlı Yarış Testi (Manual)

Her faz sonunda **en az 1 tam yarış** gerçek oynama testi.

### 5.1 Protokol
1. F1 25'i Borderless modda aç
2. `F1Leaderboard.exe` çalıştır
3. Kariyer modunda 25% uzunluğunda bir yarış başlat
4. Random 3 pit stop yap
5. Hava koşullarını değiştir (dinamik hava açık)
6. Yarış bitmeden kapat (crash/garip davranış olursa not al)

### 5.2 Kabul kriterleri
- 0 crash
- 0 görsel bozulma
- Log'da 0 ERROR
- Kullanıcı olarak overlay'in fayda sağladığını hissediyor musun? (subjektif)

## 6. Ne test ETMİYORUZ

Açıkça non-goal:
- Çoklu oyuncu yarış senkronizasyonu
- Xbox/PS/Game Pass davranışı
- 1080p/1440p görsel kalitesi (MVP'de out-of-scope)
- Anti-cheat etkileşimi (kariyer modu offline)
- DRS, MFD gibi diğer HUD elementleri
- Multi-monitor kurulumlar

## 7. Hata Raporlama

- Log dosyası: `logs/overlay.log`
- Crash sonrası: `logs/crash_YYYY-MM-DD_HHMMSS.log` — traceback + son 100 paket
- Kullanıcı raporlayacaksa: bu iki dosya + F1 25 UDP ayarları screenshot

## 8. Regression Koruması

Yeni bir faza geçerken **önceki faz'ın DoD'u tekrar koşulmalı**. Örneğin F5 hava paneli eklendikten sonra:
- [ ] F4 leaderboard hâlâ hatasız mı?
- [ ] F3 click-through hâlâ çalışıyor mu?
- [ ] F2 parser unit testleri geçiyor mu?

Bu bir "test suite" değil ama zihinsel bir checkpoint — **bir şey düzelttin, iki şey bozuldu**'yu önler.
