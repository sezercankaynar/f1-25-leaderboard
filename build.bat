@echo off
REM Tam uygulama paketleme (Windows x64).
REM Cikti: overlay\release\F1-25-Leaderboard-Overlay-win32-x64\
REM Icindeki F1-25-Leaderboard-Overlay.exe calistirilabilir.

setlocal
set ROOT=%~dp0
set ROOT=%ROOT:~0,-1%
set DEST=%ROOT%\overlay\release\F1-25-Leaderboard-Overlay-win32-x64\resources

echo.
echo ============================================
echo  1/3  Python backend (PyInstaller)
echo ============================================
if not exist "%ROOT%\.venv\Scripts\pyinstaller.exe" (
  echo [HATA] PyInstaller bulunamadi: %ROOT%\.venv\Scripts\pyinstaller.exe
  echo Once ".venv\Scripts\pip install pyinstaller" calistir.
  exit /b 1
)
if exist "%ROOT%\build\backend" rmdir /s /q "%ROOT%\build\backend"
if exist "%ROOT%\build\backend_work" rmdir /s /q "%ROOT%\build\backend_work"
if exist "%ROOT%\build\backend_spec" rmdir /s /q "%ROOT%\build\backend_spec"
"%ROOT%\.venv\Scripts\pyinstaller.exe" ^
  --onefile ^
  --name f1-leaderboard-backend ^
  --distpath "%ROOT%\build\backend" ^
  --workpath "%ROOT%\build\backend_work" ^
  --specpath "%ROOT%\build\backend_spec" ^
  --paths "%ROOT%" ^
  --noconfirm ^
  "%ROOT%\scripts\backend_entry.py"
if errorlevel 1 (
  echo [HATA] Backend build basarisiz.
  exit /b 1
)

echo.
echo ============================================
echo  2/3  Electron paketleme (electron-packager)
echo ============================================
pushd "%ROOT%\overlay"
call npm run pack
set ERR=%ERRORLEVEL%
popd
if not "%ERR%"=="0" (
  echo [HATA] Electron packager basarisiz.
  exit /b %ERR%
)

echo.
echo ============================================
echo  3/3  Backend exe ve config kopyalama
echo ============================================
if not exist "%DEST%" (
  echo [HATA] Paketlenmis resources klasoru bulunamadi: %DEST%
  exit /b 1
)
copy /y "%ROOT%\build\backend\f1-leaderboard-backend.exe" "%DEST%\f1-leaderboard-backend.exe" >nul
if errorlevel 1 exit /b 1
if exist "%DEST%\config" rmdir /s /q "%DEST%\config"
xcopy "%ROOT%\config" "%DEST%\config" /E /I /Y /Q >nul
if errorlevel 1 exit /b 1

echo.
echo ============================================
echo  TAMAMLANDI
echo ============================================
echo Packaged app: overlay\release\F1-25-Leaderboard-Overlay-win32-x64\
echo Calistir:     F1-25-Leaderboard-Overlay.exe
echo.
echo Dagitim icin klasoru ziple veya Inno Setup ile installer olustur.
endlocal
