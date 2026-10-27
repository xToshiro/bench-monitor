#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flash_monitor.py - Utilitário de Gravação e Monitoramento Serial para ESP32-C5 Bancada
Suporta gravação via PlatformIO CLI e monitoramento interativo na porta COM9.
"""

import sys
import os
import time
import argparse
import subprocess

DEFAULT_PORT = "COM9"
DEFAULT_BAUD = 115200

def get_pio_executable():
    """Localiza o binário executável do PlatformIO no perfil do usuário."""
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    candidates = [
        os.path.join(home, ".platformio", "penv", "Scripts", "pio.exe"),
        os.path.join(home, ".platformio", "penv", "bin", "pio"),
        "pio"
    ]
    for c in candidates:
        if os.path.exists(c) or c == "pio":
            return c
    return "pio"

def run_build():
    """Executa a compilação do firmware."""
    pio = get_pio_executable()
    print("🔨 [BUILD] Compilando firmware para ESP32-C5...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [pio, "run"]
    res = subprocess.run(cmd, env=env)
    return res.returncode == 0

def run_flash(port=DEFAULT_PORT):
    """Grava o firmware compilado no ESP32-C5 via porta serial."""
    pio = get_pio_executable()
    print(f"⚡ [FLASH] Gravando firmware na porta {port}...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [pio, "run", "-t", "upload", "--upload-port", port]
    res = subprocess.run(cmd, env=env)
    return res.returncode == 0

def run_monitor(port=DEFAULT_PORT, baud=DEFAULT_BAUD):
    """Conecta ao ESP32-C5 e monitora o fluxo serial e telemetria JSON."""
    try:
        import serial
    except ImportError:
        print("⚠️ pyserial não encontrado. Instalando pyserial temporariamente...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyserial"])
        import serial

    print(f"📡 [MONITOR] Conectando à porta {port} a {baud} bps (Ctrl+C para sair)...")
    try:
        ser = serial.Serial(port, baud, timeout=1.0)
        # Pulso suave de reset
        ser.setDTR(False)
        ser.setRTS(True)
        time.sleep(0.1)
        ser.setRTS(False)
        time.sleep(0.5)
        ser.reset_input_buffer()

        print("✅ Conectado com sucesso! Aguardando dados...\n")

        while True:
            line = ser.readline().decode("utf-8", errors="replace").strip()
            if not line:
                continue

            # Formatação visual amigável para mensagens de telemetria
            if line.startswith("{") and line.endswith("}"):
                print(f"📊 [TELEMETRIA JSON] {line}")
            elif "[I2C]" in line:
                print(f"🔍 {line}")
            elif "[OLED]" in line:
                print(f"🖥️  {line}")
            elif "[BME280]" in line:
                print(f"🌡️  {line}")
            else:
                print(f"   {line}")

    except KeyboardInterrupt:
        print("\n🛑 Monitoramento encerrado pelo usuário.")
    except Exception as e:
        print(f"❌ Erro de comunicação serial: {e}")

def main():
    parser = argparse.ArgumentParser(description="ESP32-C5 Bancada Flash & Monitor Utility")
    parser.add_argument("--port", default=DEFAULT_PORT, help="Porta serial COM do ESP32-C5 (padrão: COM9)")
    parser.add_argument("--build", action="store_true", help="Executa apenas a compilação")
    parser.add_argument("--flash", action="store_true", help="Executa compilação e gravação")
    parser.add_argument("--monitor", action="store_true", help="Abre apenas o monitor serial")
    parser.add_argument("--all", action="store_true", help="Compila, grava e abre o monitor serial")

    args = parser.parse_args()

    if args.all or (not args.build and not args.flash and not args.monitor):
        if run_build() and run_flash(args.port):
            time.sleep(1.0)
            run_monitor(args.port)
    elif args.build:
        run_build()
    elif args.flash:
        if run_build():
            run_flash(args.port)
    elif args.monitor:
        run_monitor(args.port)

if __name__ == "__main__":
    main()
