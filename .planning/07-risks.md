# 07 — Riskler, Bilinmeyenler, Tamir Planları

Her risk için **etki**, **olasılık**, **azaltma planı**, ve **acil durum planı (plan B)** var. Risk matrisinde sıralama: olasılık × etki.

## 🔴 Yüksek Risk

### R1 — F1 25 UDP spec'i 2025 sürümünde bozucu değişiklik içeriyor
**Etki:** Tüm parser yeniden yazılır, 1-2 gün kayıp.
**Olasılık:** Orta. F1 23→24'te birkaç alan değişti ama majör bozulma nadir.
**Azaltma:**
- Araştırma fazında EA forum PDF'ini bul ve F1 24 spec'i ile diff'le
- Base olarak sıfırdan yazma yerine olgun bir Python kütüphanesi fork et (f1-2020-telemetry vs.) — toplulukla uyumlu kalır
- Parser'da "strict" değil "lenient" parse — bilinmeyen alanları skip et, panic etme

**Plan B:** Spec yoksa bir community repo'sunu referans al (GitHub'da genelde bir-iki hafta içinde çıkar), gerekirse Wireshark ile paket boyutlarını manuel eşle.

### R2 — Yerel leaderboard'un 4K piksel konumu EA patch'lerinde kayabilir
**Etki:** Overlay hizalaması bozulur, pikselce bindirme yerine 5-10 px ofset görünür.
**Olasılık:** Düşük-Orta. EA, HUD'u major patch'lerde nadiren hareket ettirir ama mümkün.
**Azaltma:**
- Piksel ölçümlerini `layout.json`'a koy — kullanıcı yeniden ölçüp güncelleyebilsin
- `--debug` modunda bounding box çizimi — hizalama doğrulaması 10 saniyede yapılır
- Versiyon notunda "F1 25 build X.Y ile test edildi" yaz

**Plan B:** Otomatik kalibrasyon aracı — ekran görüntüsü al, yerel leaderboard'un kenarlarını edge detection ile bul ve koordinatları öner. M6 sonrası, gerçekten gerekirse.

### R3 — AI sürücülerinin ERS verisi gerçekçi değil
**Etki:** Leaderboard ERS bar'ları anlamsız olur — sadece oyuncunun bar'ı gerçekçi, 21 tanesi sabit görünebilir.
**Olasılık:** Orta. F1 oyunlarında AI bazı sistemleri basitleştirilmiş simüle eder.
**Azaltma:**
- Araştırma fazında birkaç AI aracın `ersStoreEnergy` değerinin zaman içinde değişip değişmediğini doğrula
- Değişmiyorsa: ERS bar'ını sadece oyuncu ve yakın rakipler için göster, diğerlerinde `--` yaz

**Plan B:** ERS bar'ı tamamen kaldır, yerine sadece "compound + lap" göster. Kullanıcıyı aldatmak yok — yanlış veri göstermek yerine göstermemek iyi.

## 🟠 Orta Risk

### R4 — PyQt6 şeffaf pencere fullscreen exclusive modda görünmüyor
**Etki:** Kullanıcı oyunu borderless'a almak zorunda kalır.
**Olasılık:** Yüksek. PyQt overlay'i fullscreen exclusive oyunların altında kalır — bu bilinen bir sınırlama.
**Azaltma:**
- README'de kırmızı uyarı: "F1 25 → Graphics → Display Mode → **Borderless Fullscreen**"
- Uygulama başlarken oyunu tespit etmeye çalışsın (process listesinde `F1_25.exe` var mı), yoksa pop-up ile uyar

**Plan B:** C++ + Direct3D overlay'e geç (büyük yeniden yazım) — MVP için kabul edilmez. Kullanıcıya borderless zorunluluğu dokümanla iletmek yeterli.

### R5 — EA Anti-Cheat veya EA App overlay'i şüpheli görür
**Etki:** Kariyer modunda sorun olmaması beklenir (offline) ama EA App telemetri çıkışını bloklayabilir.
**Olasılık:** Düşük. Overlay, oyuna hiç dokunmuyor, sadece UDP yayınını dinliyor — meşru bir kullanım.
**Azaltma:**
- UDP yayını F1 25'in resmi özelliği, oyun ayarlarından açılır → EA bunu kendi özelliği olarak sunuyor
- Uygulama herhangi bir memory read/write yapmıyor
- README'de "bu bir harici overlay'dir, oyun dosyaları değişmez" vurgusu

**Plan B:** Yok — bu risk gerçekleşirse EA'nin politikası değişmiş demektir, o zaman alternatif overlay yöntemleri düşünülür.

### R6 — Hava paneli için logo alanının hemen altında yeterli boşluk yok
**Etki:** Panel ya logonun üstüne biner ya leaderboard'a girer → çirkin görünür.
**Olasılık:** Orta. F1 25 HUD'u sıkışık olabilir.
**Azaltma:**
- Araştırma fazında gerçek ölçüm — en başta bu doğrulanmalı
- Panel dikey boyutu 40-64 px arası ayarlanabilir (config'de)

**Plan B:** Hava panelini farklı bir yere taşı — sağ alt köşe, saat ikonlarının yanı. Kullanıcıya sor, config'de `weather_panel.position` seçilebilsin ("top", "right_bottom", "hidden").

## 🟡 Düşük Risk

### R7 — Titillium Web fontu yüklü değilse görsel bozulur
**Etki:** Fallback Arial ile yazı biçimi değişir, hizalama bozulabilir.
**Olasılık:** Çok yüksek. Kullanıcının çoğunda font yüklü değildir.
**Azaltma:**
- Font'u `assets/fonts/TitilliumWeb-*.ttf` olarak uygulamayla paketle
- PyQt'nin `QFontDatabase.addApplicationFont()` ile runtime'da yükle
- Kullanıcı sisteminde olmasa bile uygulamaya yüklenmiş kalır

**Plan B:** Yok, plan A zaten çözüm.

### R8 — 22 araç render'ı QPainter için yavaş
**Etki:** 20 Hz hedefi tutturulamaz, overlay laggy görünür.
**Olasılık:** Düşük. QPainter 22 basit satır için fazlasıyla hızlı (milisaniye cinsinden).
**Azaltma:**
- Performans testi F4 DoD'unda zorunlu
- Yavaşlarsa: QGraphicsView'a veya native OpenGL widget'ına geç

**Plan B:** Render 20 Hz → 10 Hz'e düşür. Gözle fark edilmez.

### R9 — Pit status ve penalti bilgileri UDP spec'te farklı alanlarda
**Etki:** Yanlış görselleştirme — pit'te olmayan araç pit'te görünür vb.
**Olasılık:** Düşük. Alanlar yıllardır stabil.
**Azaltma:** Unit test ile her durum doğrula.

**Plan B:** Bu göstergeleri MVP dışına çıkar, M6 cila'ya ertele.

## 🟢 Çok Düşük Risk / Bilmemeye Razıyım

### R10 — Kullanıcı bazen overlay'i gizlemek isteyebilir (replay, screenshot)
- Çözüm: Hotkey toggle. F6'da var.

### R11 — Log dosyası diski doldurur
- Çözüm: Rotating log, F6'da var.

### R12 — 2025 takım renkleri değişirse
- Çözüm: `teams.json`'da hex, kullanıcı 1 dakikada günceller.

## Bilinmeyenler (Known Unknowns)

Araştırma fazı sonunda aydınlatılması gereken sorular — `01-research.md` ile çapraz referans:

1. F1 25 UDP format numarası kesin `2025` mi?
2. `rainPercentage` gerçek bir alan mı yoksa weather enum'dan mı türüyor?
3. `tyresAgeLaps` AI araçlar için de geliyor mu yoksa sadece oyuncu mu?
4. 2025 grid'indeki takım ID'leri nelere map'leniyor? (Cadillac, Audi ne zaman giriyor?)
5. F1 logosunun 4K'daki tam koordinatları nedir?
6. Leaderboard satır yüksekliği 60 px mı 66 px mi 70 px mi?
7. Pause'daki HUD ile yarıştaki HUD tamamen aynı mı (arka plan opacity vb.)?

Bu sorular **F4 öncesinde** yanıtlanmadıysa F4 başlanmasın — çünkü hepsi piksel hassas işler.

## Unknown Unknowns

Bilemeyeceğimiz bir dizi şey olacak. Örneğin:
- EA'in bir sonraki patch'i UDP çıkışını farklı port'a taşır mı? Taşırsa config'de port değiştirilebilsin, öğrendik.
- F1 25'te yeni bir mod (örn. sprint qualifying) farklı paketler mi atar? Muhtemelen aynı paketler farklı değerlerle.

Bu risklere karşı tek savunma: **küçük, test edilebilir parçalar** ve **rollback edilebilir commit'ler**. Replay altyapısı sayesinde bir senaryoyu tekrar oynatabilmek, bu riskleri taşınabilir kılar.

## Risk Gözden Geçirme

Her faz DoD'unda bu doküman tekrar açılıp:
- Gerçekleşen riskler `✅ gerçekleşti, X yapıldı` olarak işaretlensin
- Yeni riskler eklensin
- Gerçekleşmeyenler sadelensin

Kapalı bir risk listesi değil, canlı bir doküman.
