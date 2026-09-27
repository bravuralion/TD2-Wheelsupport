@echo off
title G29 Fahrschalter fuer Train Driver 2
cd /d "%~dp0"

echo ============================================
echo   G29 Fahrschalter fuer Train Driver 2
echo ============================================
echo.

REM ---- Python vorhanden? ----
where python >nul 2>nul
if errorlevel 1 (
    echo FEHLER: Python wurde nicht gefunden.
    echo.
    echo Bitte Python installieren - siehe Anleitung.md, Schritt 2.
    echo Wichtig: beim Installieren den Haken "Add python.exe to PATH" setzen!
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%p in ('python -c "import sys; print(sys.executable)"') do (
    echo Python: %%p
    echo (GENAU diesen Pfad in HidHide unter "Applications" eintragen - siehe Anleitung, Schritt 5)
)
echo.

REM ---- Abhaengigkeiten pruefen, bei Bedarf installieren ----
python -c "import sdl2, hid" >nul 2>nul
if errorlevel 1 (
    echo Erster Start: benoetigte Pakete werden installiert ...
    echo (das dauert einen Moment und braucht Internet)
    echo.
    python -m pip install --upgrade pip >nul 2>nul
    python -m pip install pysdl2 pysdl2-dll hidapi
    if errorlevel 1 (
        echo.
        echo FEHLER: Die Pakete konnten nicht installiert werden.
        echo Bitte Internetverbindung pruefen und Start.bat erneut ausfuehren.
        echo.
        pause
        exit /b 1
    )
    echo.
    echo Installation fertig.
    echo.
)

REM ---- Skript starten ----
echo Starte ... (Beenden mit Strg+C oder Fenster schliessen)
echo.
python g29_detent_test.py

echo.
echo Programm beendet.
pause
