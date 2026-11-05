@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

rem Lokal server CSS, JavaScript va shriftlarni ham taqdim etishi uchun.
set DEBUG=1

echo ===============================================
echo   Chilonzor - karta bloklash - lokal ishga tushirish
echo ===============================================
echo.

rem --- 1. Windows uchun Python topish ---
set PYEXE=
py -3 --version >nul 2>&1 && set PYEXE=py -3
if not defined PYEXE (python --version >nul 2>&1 && set PYEXE=python)
if not defined PYEXE (
  echo [XATO] Windows uchun Python topilmadi.
  echo Yuklab oling: https://www.python.org/downloads/
  echo Ornatishda "Add python.exe to PATH" katagini belgilang.
  pause & exit /b 1
)
echo [1/4] Python: %PYEXE%
%PYEXE% --version

rem --- 2. Windows venv (papkadagi venv Linux uchun, ishlamaydi) ---
if not exist "winenv\Scripts\python.exe" (
  echo [2/4] winenv yaratilmoqda...
  %PYEXE% -m venv winenv || (echo [XATO] venv yaratilmadi & pause & exit /b 1)
) else (
  echo [2/4] winenv mavjud
)
set PY=winenv\Scripts\python.exe

rem --- 3. Kutubxonalar ---
echo [3/4] Kutubxonalar tekshirilmoqda...
"%PY%" -c "import django,jazzmin" >nul 2>&1
if errorlevel 1 (
  echo      ornatilmoqda ^(bir marta, internet kerak^)...
  "%PY%" -m pip install --upgrade pip -q
  "%PY%" -m pip install -r requirements.txt || (echo [XATO] pip install & pause & exit /b 1)
) else (
  echo      hammasi joyida
)

rem --- 4. Migratsiya + server ---
echo [4/4] Migratsiya...
"%PY%" manage.py migrate || (echo [XATO] migrate & pause & exit /b 1)
echo.
echo ===============================================
echo   Manzil:  http://127.0.0.1:8000/apk/works/
echo   Toxtatish: Ctrl+C
echo ===============================================
echo.
start "" http://127.0.0.1:8000/apk/works/
"%PY%" manage.py runserver 127.0.0.1:8000
pause
