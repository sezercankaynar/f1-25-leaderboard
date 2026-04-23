# F1 25 Leaderboard Overlay — ROADMAP

## Projenin Tek Cümle Özeti
F1 25 kariyer modu yarışlarında, oyunun sol tarafındaki yerel leaderboard'un üstüne pikselce oturan; batarya seviyesi, lastik bilgisi (compound + o lastikle atılan tur sayısı), lastik aşınma yüzdesi ve üst kısımda hava durumu panelini (pist/hava sıcaklığı + yağış oranı) gösteren; UDP telemetri ile beslenen harici bir Python/PyQt overlay uygulaması.

## Karar Özeti (Discuss Fazından)

| Karar | Seçim | Gerekçe |
|---|---|---|
| Teknik yaklaşım | Harici overlay (UDP telemetri) | Oyun dosyasına dokunmaz, EA güncellemelerine dayanıklı, anti-cheat riski yok |
| Tech stack | Python 3.11+ + PyQt6 | Hızlı geliştirme, olgun F1 UDP kütüphaneleri, şeffaf pencere desteği |
| Yerleşim | Yerel HUD'un üstüne bindir | HUD ayarı değiştirmeye gerek yok, kurulum tek tık |
| Platform | EA App (PC) | Kullanıcının oynadığı tek platform; UDP çıkışı standart |
| Hedef çözünürlük | 3840x2160 (4K) | Ana hedef — 1080p/1440p ölçekleme sonraki faz |
| Hedef kitle | Kişisel + birkaç arkadaş | Installer ya da Nexus paketi yok; ZIP + README yeterli |

## Hedefler (Goal-Backward Tanım)

### Yarış içinde tamamlandığında gördüklerin
1. F1 25 kariyer modunda bir yarış başlatırsın
2. Arka planda `F1Leaderboard.py` çalışır
3. Oyunun sol leaderboard'unun tam üstünde bizim overlay oturur
4. Her satırda: **Poz | Takım rengi | 3 harfli sürücü kodu | ERS barı | Lastik rozeti + tur | Aşınma bar**
5. F1 logosunun altında yatay bir hava paneli: **🌡️ Track 38°C | 💨 Air 24°C | 🌧️ Rain 15%**
6. Veriler 10-20 Hz arasında canlı güncellenir (UDP feed'in verdiğinden)
7. Fark edilir bir FPS düşüşü yok (hedef: <2 FPS kayıp)

### Başarı Kriterleri
- UDP telemetri bağlantısı düşerse overlay grayscale'e döner ama çökmez
- Pit'teki araç rozeti farklı görünür (yerel HUD davranışıyla tutarlı)
- 22 araç dolu grid'de de 2 araç kalmış durumda da doğru render eder
- Uygulamayı Ctrl+Shift+F1 ile gizle/göster
- Overlay alt-tab sonrasında pozisyonunu korur

## Kilometre Taşları

| # | Kilometre Taşı | Çıktı | Doğrulama |
|---|---|---|---|
| M1 | UDP bağlantısı yerine geldi | `udp_listener.py` — 2025 spec'e uygun paket parse | Oyunda yarış başlat, konsola poz verisi yazsın |
| M2 | Veri modeli katmanı | `race_state.py` — tüm sürücüler için anlık state | Test: pickle'dan feed replay et, 20 saniye tutarlı snapshot |
| M3 | Minimal görsel overlay | Yalnız pozisyon + sürücü adı gösteren şeffaf pencere | Gerçek yarışta pozisyonla senkron çalışsın |
| M4 | Tam leaderboard | ERS barı + lastik rozeti + tur + aşınma | 4K'da piksel hizalaması yerel HUD ile ±2px |
| M5 | Hava paneli | Logonun altında sıcaklık + yağış paneli | Yağmurlu yarışta rain% güncel |
| M6 | Cila + yaşam kalitesi | Hotkey, tema config, build script, README | Tek ZIP → PC'ye çıkar → çalıştır akışı |

## Tahmini Süre
Kişisel proje varsayımı, aktif kodlama saatleri:
- M1 UDP bağlantısı: 4-6 saat
- M2 Veri modeli: 3-4 saat
- M3 Minimal overlay: 4-6 saat
- M4 Tam leaderboard: 8-12 saat (en büyük görsel iş)
- M5 Hava paneli: 2-3 saat
- M6 Cila: 3-5 saat
- **Toplam:** 24-36 saat kodlama + test

## Dışarıda Kalan (Non-Goals)
- Çoklu oyuncu yarışlarında senkronizasyon (sadece kariyer)
- Xbox/PlayStation/Xbox Game Pass PC desteği
- 1080p ve 1440p ölçekleme (ileride eklenecek, M4'te düşünülecek ama yapılmayacak)
- F1 24 veya önceki sürüm backward uyumluluk
- Yerel HUD'u gizleme (bindirme yaklaşımı seçildi)
- Başka HUD elementleri (örn. telemetri şeridi, MFD) — sadece leaderboard

## Döküman Haritası
- `01-research.md` — UDP spec, benzer mod örnekleri, HUD ölçüleri
- `02-architecture.md` — Modül yapısı, thread modeli, veri akışı
- `03-technical-spec.md` — Paket parse detayları, veri modeli, hesaplamalar
- `04-ui-design.md` — 4K piksel koordinatları, renk/tipografi, mockup
- `05-phases.md` — Faz faz iş kırılımı, tasklar, DoD
- `06-testing.md` — UDP replay altyapısı, gerçek yarış test planı
- `07-risks.md` — Bilinmeyenler, kırılma senaryoları, tamir planları
