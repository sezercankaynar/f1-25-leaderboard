# Yeni Oturum Başlatma Komutu

Bu dosya yeni oturumda Claude'a verilecek ilk prompttur. İçeriği kopyalayıp yapıştırın veya `@.planning/NEXT_SESSION.md` olarak referansla.

---

## Kopyala-Yapıştır Prompt

```
F1 25 leaderboard projesinde Faz 4 (Sıralama Tablosu) Adım 4 — Widget Rewrite
aşamasına devam ediyoruz.

Önce hafıza sistemini (MEMORY.md + bağlı dosyalar) oku — özellikle:
- feedback_no_gsd.md → /gsd:* KOMUTLARI KULLANMA; doğrudan Edit/Write ile geliştir
- project_f4_scope_revision.md → F4 kapsamı (hedef görsel example.png)
- project_f4_step1_logos.md → Adım 1 ÇIKTISI (10 logo config/assets/teams/0-9.png)
- project_f4_step2_deferred.md → Adım 2 Adım 4'e birleştirildi (team bar rengi bug)
- project_f4_step3_parser.md → Adım 3 ÇIKTISI (parser sector + delta_ms ekledi)
- feedback_assets_and_scope.md → küçük doğrulanabilir adım tercihi

Bu oturumda Adım 4'ün implementasyonuna başla. Adım 4 = F4'ün en büyük parçası,
widget'ı baştan yaz. Alt-parçalara bölerek ilerle, her alt-parça bitince kullanıcı
onayı bekle. Her alt-parça bitince hafızaya yaz.
```

---

## Durum (2026-04-22 sonu)

### Tamamlanan Adımlar
- **Adım 1 ✓** — 10 takım logosu `config/assets/teams/{0-9}.png` (1.5-4.4 KB, 64×64, şeffaf); `config/teams.json`'a `logo_path` alanı eklendi; `scripts/download_team_logos.py` kalıcı helper.
- **Adım 2 ~~(iptal)~~** → Adım 4'e birleştirildi. Teşhis: UDP team_id doğru (0-9 F1 25 spec), bug widget render pipeline'ında. Adım 4 rewrite'ında natural çözülür.
- **Adım 3 ✓** — Parser genişletildi:
  - `packet_parser.py`: `LapEntry.delta_to_car_in_front_ms` (offset 14 u16 + 16 u8 → combined ms)
  - `race_state.py`: `Driver.current_sector`, `Driver.delta_to_ahead_ms` (Optional, None=lider)
  - `dev_tools/inspect_capture.py`: `sec` + `delta_ms` kolonları
  - `captures/race_01.bin` ile doğrulandı (regression yok, parsed_ok=4812)

### Kalan: Adım 4 — Widget Rewrite (en büyük parça)

**Hedef:** `leaderboard_widget.py`'yi hedef görsel `example.png`'ye uygun dizilime yeniden yaz.

**Yeni kolon dizisi (soldan sağa):**
1. Pozisyon (lider sarı dolgu kutu + siyah yazı; diğerleri transparan + beyaz)
2. **Takım renk barı** (opak, teams.json'dan; bar çizimi zebra/highlight'lardan etkilenmesin)
3. **Takım logosu** (QPixmap cache, uygulama başında yükle, drawPixmap)
4. Sürücü 3-harf kodu
5. **Sektör mini-barları** (3 dikey dikdörtgen):
   - `d.current_sector == 0` → S1 mor, S2-S3 gri
   - `d.current_sector == 1` → S1 yeşil, S2 mor, S3 gri
   - `d.current_sector == 2` → S1-S2 yeşil, S3 mor
6. **Gap metni** — helper `format_gap(delta_ms, own_lap, leader_lap)`:
   - position==1 → `LEADER`
   - lap farkı ≥1 → `+1 LAP` / `+N LAPS`
   - else → `+{delta_ms/1000:.3f}` (örn. `+0.312`)
   - delta==0 ve position>1 → `—`
7. **Lastik rozeti** (34 px daire + compound harfi, `tire_compounds.json`) + `L##` ömür

**Çıkacak / ertelenen:**
- ERS barı — F4'ten çıkarıldı
- Aşınma barı — F4'ten çıkarıldı
- Pit turuncu highlight — kalabilir ama team bar'ı MASKE ETMESİN
- Penalti chip — şu an değil, F6 cilası

**Dikkat edilecekler:**
- **Team bar rengini maskeleme:** Zebra/player_hl/pit_hl overlay'leri `fillRect(QRectF(team_bar_w, y, w - team_bar_w, rh))` — bar'ı hariç tut. Aksi halde Adım 2'deki sönük renk bug'ı tekrarlar.
- **Layout:** `config/layout.json` güncelle — yeni kolon offset'leri (`04-ui-design.md` referans), row_height 80 (4K base) korunur.
- **Logo:** Red Bull logosu yatay geniş (64×64 kutuya dikey küçük sığıyor), Adım 1 notunda belirtildi. Gerekirse satır içi 80×48 dikdörtgene çevir.

**Alt-parça önerisi (kullanıcı küçük adım tercihi):**
1. **4a — Layout + team bar fix:** layout.json yeni kolonlar + widget'ın row çizim pipeline'ını yeniden düzenle (team bar'ı opak bırak, overlay'leri bar'ın sağına sınırla). Screenshot al, `example.png` ile karşılaştır.
2. **4b — Logo kolonu:** QPixmap cache helper + drawPixmap row içinde. 10 sürücü + logo renderı testi.
3. **4c — Sektör mini-barları:** 3 dikey dikdörtgen çiz, `current_sector` mantığı.
4. **4d — Gap kolonu + format_gap helper:** lap-down algılama için leader position lookup.
5. **4e — Lastik rozeti + `L##`:** `tire_compounds.json` renkleri, compound harfi.
6. **4f — Final screenshot + `example.png` karşılaştırma:** UAT; gerekirse fine-tune.

Her alt-parça sonunda kullanıcı onayı + hafızaya yaz (project_f4_step4a.md, vs.).

---

## F5 ve F6 (F4 sonrası)

- **F5** — Başlık bandı (F1 logo + session type + LAP N/M) + hava paneli (pist/hava/yağış)
- **F6** — Cila: hotkey, tray icon, PyInstaller build, README, purple/green sektör konvansiyonu (opsiyonel, SessionHistory paketi gerekir)

---

## Hafıza Sistemi

`C:\Users\Sezer\.claude\projects\C--Users-Sezer-Desktop-f1-25-leaderboard-patch\memory\`

Yeni oturumda `MEMORY.md` otomatik yüklenir. **feedback_no_gsd.md** kritik: `/gsd:*` komutları kullanılmaz, doğrudan Edit/Write ile geliştir.

### Her adım sonunda

Hafızaya `project_f4_step{N}.md` yaz + MEMORY.md indeksine bir satır ekle. Oturum yarıda kalırsa bu `NEXT_SESSION.md`'yi güncelle.
