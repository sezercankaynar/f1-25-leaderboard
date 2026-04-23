# 01 — Araştırma Fazı

Bu doküman implementasyona başlamadan önce doğrulanması gereken bilgileri ve yapılacak araştırma adımlarını içerir. **Her madde bir soru**. Yanıtlar bulundukça bu dokümana yazılır.

## 1. F1 25 UDP Telemetri Spec'i

### 1.1 Spec erişimi
- **Soru:** Codemasters/EA, F1 25 için resmi UDP telemetri spec'ini yayınladı mı?
- **Kaynak:** https://forums.ea.com/ → F1 25 Data Output kategorisi (F1 2020'den beri geleneksel yayın noktası)
- **Yedek kaynak:** GitHub'da `F1-25-UDP-Documentation` veya topluluk repoları
- **Beklenti:** F1 24 spec'inin %90+ geriye uyumlu olması (her yıl küçük ekler, nadiren breaking change)
- **Aksiyon:** PDF'i indir, `.planning/reference/F1_25_UDP_Specification.pdf` olarak sakla

### 1.2 İhtiyaç duyulan paket türleri
Bu projenin tüm UI verisi aşağıdaki paketlerden gelir:

| Paket ID | İsim | Frekans | Ne için kullanılacak |
|---|---|---|---|
| 1 | Session | 2 Hz | Pist sıcaklığı, hava sıcaklığı, yağış oranı, weather forecast |
| 2 | Lap Data | 60 Hz | Sürücü pozisyonu, mevcut tur no, pit durumu, penaltiler |
| 4 | Participants | 1 Hz | Sürücü adı, takım ID, 3 harf kodu (VER/HAM/LEC...) |
| 6 | Car Telemetry | 60 Hz | (Opsiyonel: gerekli değilse bu paketi dinlemeyelim, CPU tasarrufu) |
| 7 | Car Status | 10 Hz | ERS enerji deposu (`ersStoreEnergy`), current tire compound, tire age laps |
| 10 | Car Damage | 10 Hz | `tyresWear[4]` — her lastik köşesinin aşınma yüzdesi |

### 1.3 Her sürücü için batarya gerçekten gelir mi?
- **Kritik soru:** Car Status paketi 22 araç için mi yoksa sadece oyuncu aracı için mi enerji verisi içeriyor?
- **Önceki sürümlerde:** F1 2023'ten itibaren Car Status paketi `CarStatusData[22]` dizisi halinde — TÜM araçlar için gelir ama AI araçlarında bazı alanlar simüle edilmiş olabilir
- **Doğrulama yolu:** Kariyer modunda yarış başlat, UDP'yi wireshark/python script ile dinle, 22 elemanlı dizide ersStoreEnergy alanlarının sıfır olmayan farklı değerler aldığını gör
- **Risk:** AI araçlarının ERS'i gerçekçi simüle edilmiyor olabilir (ör. sabit %50 görünüyor olabilir) → MVP'yi kırılma senaryosu olarak risks.md'de not al

### 1.4 Lastik compound kodları
F1 UDP spec'inde lastik compound'ları tipik olarak `actualTyreCompound` ve `visualTyreCompound` şeklinde iki alanda gelir:
- `actualTyreCompound`: Teknik compound (C1..C5 aralığı)
- `visualTyreCompound`: **Bizim göstereceğimiz** — Soft/Medium/Hard/Inter/Wet
  - Tipik enum: `16=Soft, 17=Medium, 18=Hard, 7=Inter, 8=Wet`
- **Aksiyon:** F1 25 spec'inde bu enum'u doğrula, `tyre_compound.py` içine map'le

### 1.5 "O lastikle atılan tur sayısı" (tyresAgeLaps)
- Car Status paketinde `tyresAgeLaps` alanı mevcut (F1 23+)
- Pit stop sonrası sıfırlanır
- **UI'da nasıl göster:** `[S] L12` formatı — S=Soft rozet rengiyle, L12=12. tur

## 2. UDP Çıkışını Açma (F1 25 Oyun Tarafı)

### 2.1 Oyun içi ayarlar
- Telemetry Settings → UDP Telemetry = **ON**
- UDP Broadcast Mode: **OFF** (localhost için gereksiz, kapalı tutulsun)
- UDP IP Address: `127.0.0.1`
- UDP Port: `20777` (varsayılan)
- UDP Send Rate: **60 Hz** (en yüksek)
- UDP Format: **2025** (en yeni)

**Aksiyon:** README'ye ekran görüntülü kurulum adımı koy.

### 2.2 EA App üzerinden çalıştığında UDP'de fark var mı?
- **Beklenti:** Launcher fark etmez, UDP soket oyun executable'ı tarafından açılır
- **Risk:** EA App'in firewall prompt'u ilk çalıştırmada gelebilir → README'de not düş

## 3. Benzer Açık Kaynak Projeler (Inspiration + Öğrenme)

Araştırılacak repo ve projeler:

| Proje | Neden bakılacak | Ne öğrenilebilir |
|---|---|---|
| `f1-telemetry-client` (NodeJS) | Olgun UDP parser | Paket struct layout'ları |
| `f1-2020-telemetry` (Python) | Python referansı | Struct unpack pattern'ları, DB recording |
| `pyf1` / `f1tenth` | - | UDP socket async patterns |
| Sim Racing Studio | Ticari overlay | UI/UX referans (bizim yapacağımızdan daha zengin ama fikir için iyi) |
| RaceLabApps | Ticari overlay | Leaderboard layoutu için karşılaştırma |

**Aksiyon:** Python ekosistemindeki en olgun UDP parser'ı base al, struct tanımlarını F1 25 spec'e göre güncelle. Sıfırdan yazmak yerine fork + güncelle yaklaşımı seçilsin — parser yazmak projenin en sıkıcı ve en çok hata yapılan kısmı.

## 4. Yerel Leaderboard'un Piksel Konumu (4K)

Overlay'i üste bindireceğimiz için yerel HUD'un 4K'daki tam konumunu ölçmemiz gerekiyor.

### 4.1 Ölçüm yöntemi
1. Kariyer modunda bir yarış başlat (aynı takım + aynı pist ile tekrarlanabilir olsun)
2. Pause ekranında F12 ile ekran görüntüsü al
3. Paint.NET veya benzer araçta leaderboard'un sol-üst ve sağ-alt köşelerini piksel olarak işaretle
4. Her satırın yüksekliğini ölç
5. Sürücü 3-harf kodu, pozisyon numarası, takım renk barı için piksel koordinatlarını kaydet

### 4.2 Ölçülmesi gereken değerler
- [ ] Leaderboard bounding box: `(x, y, width, height)` — 4K cinsinden
- [ ] Satır yüksekliği (22 sürücü için scroll yok, tek ekran mı?)
- [ ] F1 logosunun bounding box'ı (hava paneli buraya oturacak)
- [ ] Logo ile leaderboard'un ilk satırı arasındaki boşluk (hava paneli için yer)

### 4.3 Notlar
- **Ölçümler referans sayılacak, hard-code edilmeyecek** — config dosyasında `layout.json` içine yaz, ileride 1080p/1440p preset'leri kolayca eklenebilsin
- **Pause'daki HUD ile yarıştaki HUD farklı olabilir** → ölçümü yarış sırasında al (kayıt → oyun dondur → screenshot)

## 5. Windows Overlay Rendering Yöntemleri

### 5.1 Aday yöntemler
| Yöntem | Avantaj | Dezavantaj |
|---|---|---|
| PyQt6 + `Qt.WindowTransparentForInput` + `Qt.FramelessWindowHint` + `Qt.WindowStaysOnTopHint` | En kolay, tam Python içinde | Fullscreen exclusive modda görünmeyebilir |
| DXGI Desktop Duplication + DX11 overlay | En güvenilir fullscreen desteği | C++ gerekir, PyQt ile uyumsuz |
| PyQt6 + `WS_EX_LAYERED` Win32 flags | PyQt'nin doğal davranışını genişletir | Fullscreen exclusive hâlâ sorun |

### 5.2 Kritik soru: F1 25 nasıl çalışıyor — fullscreen exclusive mi borderless mı?
- **Varsayım:** Modern oyunlar genellikle borderless windowed default ya da kolay geçilebilir
- **Aksiyon:** Oyun ayarlarında Display Mode → **Borderless** önermek README'de zorunlu olsun
- **Fullscreen exclusive desteği MVP dışında** (risks.md'ye eklenmeli)

### 5.3 Click-through davranışı
Overlay tıklamaları geçirmeli — yoksa oyunda mouse etkileşimi kırılır:
- PyQt6'da `self.setAttribute(Qt.WA_TransparentForMouseEvents, True)`
- `WindowTransparentForInput` flag'i ile birlikte

## 6. Hava Paneli Veri Kaynağı

Session paketinden gelen alanlar:
- `trackTemperature` (int8, °C)
- `airTemperature` (int8, °C)
- `weather` (enum: 0=Clear, 1=Light Cloud, 2=Overcast, 3=Light Rain, 4=Heavy Rain, 5=Storm)
- `weatherForecastSamples[]` — gelecek 5/10/15/30/60 dakika öngörüsü (her biri ayrı örnek)
- **Yağış oranı (%) gerçekten bir alan mı yoksa türetilmiş mi?**
  - F1 24+'da `rainPercentage` adlı bir alan Session paketinde var (doğrulanacak)
  - Yoksa weather enum'dan türetilir: Clear=0, LightCloud=0, Overcast=5, LightRain=30, HeavyRain=70, Storm=95
  - **Aksiyon:** Spec'i kontrol et, gerçek alan varsa onu kullan, yoksa enum→yüzde tablosu yaz

## 7. Takım Renkleri

Her takımın marka rengini Participants paketindeki `teamId` üzerinden map'lemek gerek:

| teamId | Takım | Renk (2025 livery'e göre, doğrulanacak) |
|---|---|---|
| 0 | Mercedes | `#00D2BE` |
| 1 | Ferrari | `#DC0000` |
| 2 | Red Bull | `#0600EF` |
| 3 | Williams | `#00A0DE` |
| 4 | Aston Martin | `#006F62` |
| 5 | Alpine | `#0090FF` |
| 6 | RB / VCARB | `#1660AD` |
| 7 | Haas | `#B6BABD` |
| 8 | McLaren | `#FF8700` |
| 9 | Kick Sauber | `#52E252` |
| ... | | (2025 grid'ine göre güncellenecek — Cadillac, Audi girişleri?) |

**Aksiyon:** F1 25 oyunundaki gerçek takım rengi paletini UI'dan yakala (screenshot + eyedropper), kod içinde aynı hex'ler kullan.

## 8. Çıktı Tablosu (Bu dokümandan planlamaya girdi)

Araştırma tamamlandığında şu soruların net yanıtları olmalı:

- [ ] F1 25 UDP spec PDF'i elde edildi mi?
- [ ] Car Status paketi 22 araç için ERS verisi veriyor mu?
- [ ] `tyresAgeLaps` F1 25 spec'inde aynı isimle mi geliyor?
- [ ] Session paketinde `rainPercentage` alanı var mı?
- [ ] Yerel 4K leaderboard'un bounding box'ı ölçüldü mü?
- [ ] F1 logosu ile leaderboard arasındaki yüksekliğe hava paneli sığıyor mu?
- [ ] Borderless mod click-through overlay ile sorunsuz çalışıyor mu?
- [ ] Kullanılacak base UDP parser kütüphanesi seçildi mi?
- [ ] 2025 takım renkleri doğrulandı mı?

Tüm kutular işaretlenene kadar **02-architecture.md** finalize edilmesin.
