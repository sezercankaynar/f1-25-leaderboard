# 04 — UI Tasarımı ve Yerleşim

## Tasarım Felsefesi
- **Yerel F1 25 HUD estetiğini koru** — kullanıcı beyni iki farklı dil görmesin. Aynı font ailesi, aynı köşe yumuşaklığı, aynı kontrast seviyesi.
- **Az ama net bilgi** — her piksel bir işe yarasın. "Gösterelim de yer doldursun" yok.
- **Hızlı tarama** — gözün 0.3 saniyede 22 satırı tarayabilmesi için kolonların pozisyonu asla değişmesin.

## Genel Yerleşim (4K / 3840×2160)

```
                                (ekran ~3840 geniş)
┌──────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  ┌──────────────────┐                                                  │
│  │                  │ ← [80, 160] – [560, 252]                        │
│  │    F1 25 LOGO    │   logo_area (yerel)                              │
│  │                  │                                                  │
│  └──────────────────┘                                                  │
│  ┌──────────────────┐                                                  │
│  │ 🌡 38° 💨 24° 🌧 15%│ ← [80, 260] – [560, 324]  weather_panel      │
│  └──────────────────┘                                                  │
│  ┌──────────────────┐                                                  │
│  │ 1 │VER│██▓  S L12 │ ← [80, 340] – [560, 1820]  leaderboard        │
│  │ 2 │HAM│██   M L 8 │   22 satır × 66px = 1452px                    │
│  │ ...              │                                                  │
│  │ 22│SAR│▓    H L22 │                                                  │
│  └──────────────────┘                                                  │
│                                                                        │
│                          [oyun ekranının kalanı]                      │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

**Üç görsel katman:**
1. **Logo alanı** — Yerel F1 logosu, dokunmuyoruz (yerel HUD görünür kalsın)
2. **Hava paneli** — Logo ile leaderboard arasına **biz** yerleştiriyoruz, bu alan normalde boş
3. **Leaderboard** — Yerel leaderboard'un üstüne pikselce bindiriliyor

> **Kritik:** Tüm piksel değerleri 4K baseline. Araştırma fazında gerçek ölçümlerle `layout.json` güncellenecek — aşağıdaki sayılar **referans**.

## Leaderboard Satır Anatomisi

**2026-04-21 revizyonu:** Kullanıcı hedef görseli (example.png) netleştirdi. Eski anatomi (ERS barı + aşınma barı) **çıkarıldı**. Yeni kolon dizisi:

Tek satır için 4K piksel layout'u (satır yüksekliği: **80 px**):

```
  0    60   72   128            280     330      460       520
  │    │    │    │              │       │        │         │
  ▼    ▼    ▼    ▼              ▼       ▼        ▼         ▼
 ┌────┬─┬────┬──────────────────┬───────┬────────┬──────────┐
 │ P  │█│ 🛡 │  VER             │ ▊▊▊   │ +0.312 │ (S) L12  │
 │ 1  │ │    │                  │       │        │          │
 └────┴─┴────┴──────────────────┴───────┴────────┴──────────┘
  │    │  │          │              │        │        │
  │    │  │          │              │        │        │
 Pos  Team Team    Driver         Sector     Gap      Tyre
  no  bar  logo    abbr           progress   to ahead compound + lap
```

> Not: `example.png`'de her satırda iki küçük yuvarlak nokta (sağda mavi) görünüyor. Kullanıcı: **çizmeyeceğiz** (işlevsel olmadığını belirtti).

### Satır kolonları detaylı

| Kolon | x-start | Genişlik | İçerik | Veri kaynağı |
|---|---|---|---|---|
| Position | 8 | 44 | `1`, `12`, `20` — lider için sarı kutu, podyum özel | `LapData.carPosition` |
| Team bar | 60 | 8 (h 80) | Dikey renk şeridi | `Participants.teamId` → `teams.json[color]` |
| Team logo | 72 | 48×48 px | Takım logosu PNG (şeffaf) | `Participants.teamId` → `config/assets/teams/{id}.png` |
| Driver abbr | 128 | 140 | `VER`, `HAM` — 32 px SemiBold | `Participants.name` (3-harf) |
| Sector progress | 280 | 44 | 3 dikey mini-bar, geçilen sektör dolu | `LapData.sector` + `sector1TimeMSPart` + `sector2TimeMSPart` |
| Gap to ahead | 330 | 124 | `+0.312` / `+1 LAP` — 24 px Regular | `LapData.deltaToCarInFront*` |
| Tyre badge + lap | 460 | 60 (daire 34 + `L12`) | `S`/`M`/`H`/`I`/`W` rozet + ömür | `CarStatus.visualTyreCompound` + `CarDamage.tyresAgeLaps` (ya da CarStatus.tyresAgeLaps) |

### Sektör gelişimi (kolon 6) — ilk sürüm

MVP için **basit mantık**: içinde bulunduğu ve geçilen sektörler **dolu**, sonrakiler **boş**.

```
Şu an sektör 1: [▊][ ][ ]
Şu an sektör 2: [▊][▊][ ]
Şu an sektör 3: [▊][▊][▊]
```

Renk: mevcut sektör **mor** (`#9C27B0`), tamamlananlar **yeşil** (`#00E676`), gelecek **gri** (`rgba(255,255,255,0.2)`).

**F1 purple/green konvansiyonu** (en hızlı → mor, kişisel en iyi → yeşil) **F6 cila fazına ertelendi** — SessionHistory paketi + bestSectorTime takibi gerektirir, MVP karmaşası yaratır.

### Gap kolonu — format kuralları

| Durum | Format |
|---|---|
| Leader (P1) | `LEADER` |
| Normal | `+0.312`, `+12.487` (ms/1000 → 3 hane) |
| Bir tur geride | `+1 LAP` |
| İki+ tur geride | `+N LAPS` |
| Interval veri yok (yarış başı) | `—` |

### Lastik kolonu

- Rozet: 34 px çap daire, compound renk arka plan (tire_compounds.json)
- Yanında `L` + tur sayısı, örn. `L12`
- `tyresAgeLaps == 0` → `L0` göster, gri renk

### ERS barı / Aşınma barı (ESKİ anatomi) — ERTELENDİ

Faz 4'ten çıkarıldı. İleride "genişletilmiş satır modu" olarak F6'da opsiyonel gelebilir.

## Hava Paneli Anatomisi

Yatay bant, 4K'da ~480 × 64 px:

```
┌────────────────────────────────────────────────────┐
│                                                     │
│   🌡  Track 38°C      💨  Air 24°C      🌧  15%   │
│                                                     │
└────────────────────────────────────────────────────┘
```

- İkonlar: Unicode emoji ya da basit SVG path (emoji render'ı Windows'ta tutarsız, SVG tercih edilebilir — M5'te karar)
- Üç bölme eşit aralıklı (her biri ~160 px)
- Yağış oranı 50%'nin üstündeyse `🌧` ikonu pulse animasyonu yapsın (opsiyonel, M6 cila)
- Pist ısısı 45°C'nin üstünde kırmızıya, altında normal beyaz

## Renk Paleti

### Arka plan
- Leaderboard arka plan: `rgba(10, 14, 20, 0.82)` — hafif mat siyah, %18 şeffaf
- Hava paneli: Aynı arka plan, alt kenarda 1 px `rgba(255,255,255,0.1)` ayraç

### Satır durumları
| Durum | Arka plan | Not |
|---|---|---|
| Normal | Transparan | Sadece genel arka plan görünür |
| Oyuncu | `rgba(255, 235, 59, 0.15)` ince sarı vurgu | Player car |
| Pit'te | `rgba(255, 152, 0, 0.20)` turuncu | `pit_status > 0` |
| DRS aktif | (M6'ya ertelendi, MVP değil) | - |

### Takım renkleri
`config/teams.json`'dan gelir, 2025 grid'i için araştırma fazında doğrulanır.

### ERS bar
- Gradient doldurma: `#7B1FA2` → `#3F51B5`
- Boş kısım: `rgba(255,255,255,0.08)`

### Aşınma bar
| Aşınma | Renk |
|---|---|
| 0-29% | `#00E676` (yeşil) |
| 30-59% | `#FFEB3B` (sarı) |
| 60-84% | `#FF9800` (turuncu) |
| 85-100% | `#F44336` (kırmızı), pulse animasyonu |

### Lastik rozeti
| Compound | Kod | Arka plan | Metin rengi |
|---|---|---|---|
| Soft | S | `#E53935` | `#FFFFFF` |
| Medium | M | `#FDD835` | `#000000` |
| Hard | H | `#FAFAFA` | `#000000` |
| Intermediate | I | `#00C853` | `#FFFFFF` |
| Wet | W | `#1E88E5` | `#FFFFFF` |

## Tipografi

| Eleman | Font | Boyut (4K) | Ağırlık |
|---|---|---|---|
| Position no | Titillium Web | 34 px | SemiBold |
| Driver abbr | Titillium Web | 30 px | SemiBold |
| Lap on tyres | Titillium Web | 22 px | Regular |
| Weather labels | Titillium Web | 24 px | Medium |
| Weather values | Titillium Web | 28 px | SemiBold |
| Rozet harfi | Titillium Web | 22 px | Bold |

**Neden Titillium Web?** F1'in resmi fontu (ya da çok yakını). Ücretsiz, Google Fonts'ta mevcut. Yerel HUD ile görsel uyum için kritik.

**Fallback:** Arial Bold — Titillium yüklü değilse bile kırılmasın.

## Durum Göstergeleri

### Bağlantı durumu (overlay köşesinde mini)
Sağ alt köşede 8×8 px nokta:
- Yeşil: UDP paketi son 500 ms içinde geldi
- Sarı: 500-2000 ms arası
- Kırmızı: >2000 ms — bağlantı koptu, overlay grayscale'e döner

### Pit indicator
- `pit_status == 1` (pit lane'e giriyor): Pozisyon numarasının yanında küçük turuncu `P` harfi
- `pit_status == 2` (pit alanında): Satır turuncu vurgu + `P`
- `pit_status == 0`: Normal

### Penalti
Pozisyon numarasının sol üstünde mini kırmızı rozette saniye:
`+5`, `+10` vb.

## Animasyonlar

**MVP'de yok.** M6 cila fazında opsiyonel olarak:
- Pozisyon değişikliği: 200 ms ease-out kayma
- ERS bar dolma: 150 ms yumuşak geçiş
- Pit girişi: 3 frame flash

MVP statik render — performans ve basitlik için.

## Ölçeklendirme (Çoklu Çözünürlük)

MVP 4K only. Geleceği düşünerek:
- Tüm piksel değerleri `layout.json`'dan okunur
- Sabit (`row_height = 66`) değil, `scale_from_4k` fonksiyonu ile çarpılır
- 1080p ve 1440p preset'leri **M6'dan sonraki** ekleme — şimdilik yok

## Erişilebilirlik

- Renk körü mod: **MVP dışı**
- Font boyutu ayarı: **MVP dışı**
- Ama threshold'ların config'de olması ileride eklemeyi mümkün kılar

## Mockup (ASCII — gerçek tasarım aracı kullanılmayacak)

**Leaderboard tek satır, oyuncu:**
```
┌──────────────────────────────────────────────────────┐
│                                                       │
│  P1  ║ VER      [████████░░] 80%   (S) L12  ████░   │  ← sarı vurgu
│                                                       │
└──────────────────────────────────────────────────────┘
```

**Leaderboard tek satır, pit'te:**
```
┌──────────────────────────────────────────────────────┐
│                                                       │
│  P  P13 ║ HAM   [████░░░░░░] 40%   (H) L 3  ░░░░░    │  ← turuncu vurgu
│                                                       │
└──────────────────────────────────────────────────────┘
```

**Hava paneli:**
```
┌──────────────────────────────────────────────────────┐
│  🌡  Track 38°C     💨  Air 24°C     🌧  Rain 15%   │
└──────────────────────────────────────────────────────┘
```

## Sonraki Adım
UI tasarımı piksel piksel finalize edilmeden `05-phases.md`'deki M3 (minimal görsel overlay) tamamlanmamalı. Araştırma fazındaki gerçek ekran görüntüsü ölçümleri bu dökümanı günceller.
