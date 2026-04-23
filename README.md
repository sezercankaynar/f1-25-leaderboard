# F1 25 Leaderboard Overlay

F1 25 kariyer modu için harici overlay uygulaması. Yerel leaderboard'un üstüne batarya, lastik, aşınma ve hava bilgisi ekler.

## Kurulum

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## F1 25 UDP Ayarları

Oyunda: Settings → Telemetry Settings
- UDP Telemetry: **ON**
- UDP IP: `127.0.0.1`
- UDP Port: `20777`
- UDP Send Rate: **60 Hz**
- UDP Format: **2025**
- Display Mode: **Borderless Fullscreen** (zorunlu)

## Çalıştırma

```bash
python -m f1_leaderboard.app
```

## Hotkey'ler

| Tuş | Aksiyon |
|---|---|
| Ctrl+Shift+F1 | Overlay göster/gizle |
| Ctrl+Shift+Q | Uygulamayı kapat |

## Geliştirme

Detaylı plan için `.planning/` klasörüne bakın.
