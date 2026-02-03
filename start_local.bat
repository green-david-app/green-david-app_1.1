@echo off
REM Green David App - Localhost Startup Script
REM Pro Windows

echo.
echo ====================================================
echo   GREEN DAVID APP - LOCALHOST START
echo ====================================================
echo.

REM Kontrola Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python neni nainstalovany!
    echo         Nainstaluj Python3: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python nalezen
python --version
echo.

REM Kontrola Flask
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Flask neni nainstalovany, instaluji...
    pip install flask
)

echo [OK] Flask nainstalovany
echo.

REM Nastavení proměnných
set ADMIN_EMAIL=admin@greendavid.local
set ADMIN_PASSWORD=admin123
set DB_PATH=app.db

echo [CONFIG] Nastaveni:
echo          Admin email: %ADMIN_EMAIL%
echo          Admin heslo: %ADMIN_PASSWORD%
echo          Databaze: %DB_PATH%
echo.

REM Kontrola databáze
if not exist %DB_PATH% (
    echo [INFO] Vytvarim novou databazi...
) else (
    echo [INFO] Pouzivam existujici databazi: %DB_PATH%
)

echo.
echo ====================================================
echo   SERVER BEZI NA: http://127.0.0.1:5000
echo ====================================================
echo.
echo   Prihlaseni:
echo   Email: %ADMIN_EMAIL%
echo   Heslo: %ADMIN_PASSWORD%
echo.
echo   Pro zastaveni serveru zmackni CTRL+C
echo.
echo ====================================================
echo.

REM Spuštění
python main.py

pause
