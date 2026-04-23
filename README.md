# F1 25 Leaderboard Overlay

F1 25 kariyer modu için harici overlay uygulaması. Transparent, click-through ve always-on-top bir pencerede sürücü sıralaması, sektör renkleri, gap, ERS, lastik durumu gösterir. Oyunu duraklatınca / menüye girince otomatik gizlenir.

İki parçadan oluşur:
- **Python backend** — F1 25 UDP telemetri (port 20777) dinler, parse eder, WebSocket üstünden yayın yapar (port 8765)
- **Electron + React frontend** — transparent overlay penceresi, backend'e bağlanır ve Classic Broadcast tarzında render eder

## İndirip kurma (son kullanıcı)

1. [Releases](https://github.com/sezercankaynar/f1-25-leaderboard/releases) sayfasından en son sürümün `F1-25-Leaderboard-Overlay-v*-win-x64.zip` dosyasını indir
2. Zip'i istediğin klasöre çıkar
3. `F1-25-Leaderboard-Overlay.exe` dosyasını çift tıkla
4. F1 25 oyununda UDP telemetriyi aktif et:

    Settings → Telemetry Settings:
    - UDP Telemetry: **ON**
    - UDP Format: **2025**
    - UDP IP: `127.0.0.1` / Port: `20777` / Send Rate: **60Hz**
    - Display Mode: **Borderless Fullscreen** (zorunlu)

5. Oyuna gir, yarışa başla — leaderboard otomatik görünür

### Hotkey'ler

| Tuş | Aksiyon |
|---|---|
| `Ctrl+Shift+F1` | Overlay göster / gizle |
| `Ctrl+Shift+Q` | Uygulamayı kapat |

## Kaynak koddan çalıştırma (geliştirici)

### Gereksinimler

- Windows 10/11 x64
- Python 3.11+
- Node.js 20+

### Dev modu (iki terminal)

```bash
# İlk seferinde
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd overlay && npm install && cd ..
```

```bash
# Terminal 1 — Python backend
.venv\Scripts\activate
python -m f1_leaderboard.app
```

```bash
# Terminal 2 — Electron + Vite
cd overlay
npm run dev
```

### Lokal installer build

Tek komutta full paket:

```bash
build.bat
```

Bu komut:
1. `scripts/backend_entry.py` üzerinden PyInstaller ile backend exe üretir (`build/backend/`)
2. Vite ile React bundle'ı oluşturur
3. electron-packager ile Electron uygulamasını paketler (`overlay/release/`)
4. Backend exe ve config dosyalarını paketin içine kopyalar

Sonuç: `overlay/release/F1-25-Leaderboard-Overlay-win32-x64/` — doğrudan çalıştırılabilir klasör. Dağıtım için ziple veya Inno Setup ile installer üret.

## Yeni sürüm yayınlama (maintainer)

GitHub Actions `.github/workflows/release.yml` dosyası `v*` tag push'larına tepki verir:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Workflow Windows runner'da build'i otomatik yapar ve GitHub Release'i zip ekli olarak oluşturur. Manuel tetikleme için Actions sekmesinde **Release** workflow'unda "Run workflow" butonu.

## Mimari

```
F1 25 (UDP :20777) → Python backend → WebSocket :8765 → Electron renderer
                                                          ↓
                                                     React overlay
```

Detaylar: `.planning/` klasörü.

## Özellikler

- 20 sürücü leaderboard (pozisyon delta ok, takım rengi şeridi, takım logosu, 3-harf kod)
- Sektör renkleri (F1 broadcast konvansiyonu: mor/yeşil/sarı/gri)
- Tur sonu 7 saniye sektör rengi persist
- Gap / interval kolonu
- ERS deploy mode (OFF/MED/HOT/OVT) + batarya yüzdesi
- Lastik compound + aşınma halkası + lap sayacı
- FLIP animasyonu (pozisyon değişimi)
- Oyun duraklı/menüde otomatik gizlenir
