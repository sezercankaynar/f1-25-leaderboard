@echo off
REM Backend PyInstaller ile tek dosya .exe'ye paketle.
REM Cikti: build\backend\f1-leaderboard-backend.exe
REM Bu dosya proje kokundeki .venv'i kullanir.

setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\pyinstaller.exe" (
  echo [HATA] PyInstaller bulunamadi. Once ".venv\Scripts\pip install pyinstaller" calistir.
  exit /b 1
)

if exist "build\backend" rmdir /s /q "build\backend"
if exist "build\backend_spec" rmdir /s /q "build\backend_spec"

.venv\Scripts\pyinstaller.exe ^
  --onefile ^
  --name f1-leaderboard-backend ^
  --distpath build\backend ^
  --workpath build\backend_work ^
  --specpath build\backend_spec ^
  --paths . ^
  --hidden-import f1_leaderboard ^
  --hidden-import f1_leaderboard.app ^
  --hidden-import f1_leaderboard.packet_parser ^
  --hidden-import f1_leaderboard.race_state ^
  --hidden-import f1_leaderboard.snapshot_codec ^
  --hidden-import f1_leaderboard.udp_listener ^
  --hidden-import f1_leaderboard.ws_server ^
  --noconfirm ^
  scripts\backend_entry.py

if errorlevel 1 (
  echo [HATA] PyInstaller build basarisiz.
  exit /b 1
)

echo.
echo [OK] Backend exe: build\backend\f1-leaderboard-backend.exe
endlocal
