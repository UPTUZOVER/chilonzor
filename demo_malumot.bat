@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=winenv\Scripts\python.exe
if not exist "%PY%" set PY=python
echo Demo malumot yaratilmoqda...
"%PY%" manage.py migrate
"%PY%" manage.py demo_data
echo.
echo Ochirish uchun: manage.py demo_data --clear
pause
