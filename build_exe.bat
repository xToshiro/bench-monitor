@echo off
title Build BenchMonitor Executable
echo =======================================================
echo  Building Standalone BenchMonitor Executable
echo =======================================================
python -m PyInstaller --onefile --noconsole --name "BenchMonitor" --exclude-module PySide6 --exclude-module PyQt5 --exclude-module PySide2 --exclude-module matplotlib --exclude-module scipy --exclude-module IPython --exclude-module botocore --exclude-module pyarrow --hidden-import serial --hidden-import serial.tools.list_ports dashboard_qt.py
if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================
    echo  SUCCESS: Executable generated at dist\BenchMonitor.exe
    echo =======================================================
) else (
    echo.
    echo [ERROR] PyInstaller compilation failed.
)
pause
