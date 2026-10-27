# 🚀 Bench Monitor

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![SoC](https://img.shields.io/badge/Microcontroller-ESP32--C5%20(RISC--V%20240MHz)-red.svg)](https://www.espressif.com/en/products/socs/esp32-c5)
[![PlatformIO](https://img.shields.io/badge/PlatformIO-Core%206.1+-orange.svg)](https://platformio.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt6%20%2B%20pyqtgraph-brightgreen.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Author](https://img.shields.io/badge/Author-xToshiro-purple.svg)](https://github.com/xToshiro)

**Bench Monitor** is a modular, high-precision telemetry and bench validation station built around the **Espressif ESP32-C5** (32-bit RISC-V core @ 240 MHz). It integrates an on-board OLED dashboard, a shared I2C sensor bus, a dedicated UART NDIR optical Carbon Dioxide ($CO_2$) sensor, and a desktop GUI application developed in **Python (PyQt6 & pyqtgraph)** with statistical analysis and multi-format data export.

---

## 📌 Hardware Pinout & Wiring Map

```
========================================================================================
  Signal Name     ESP32-C5 Pin   Target Module Pin        Bus / Protocol   Voltage Level
========================================================================================
  I2C SDA         GPIO 8         SDA (OLED & Climate)     I2C (400 kHz)    3.3V Logic
  I2C SCL         GPIO 9         SCL (OLED & Climate)     I2C (400 kHz)    3.3V Logic
  UART RX         GPIO 5         TX (NDIR CO2 Sensor)     UART1 (9600 8N1) 3.3V Logic
  UART TX         GPIO 4         RX (NDIR CO2 Sensor)     UART1 (9600 8N1) 3.3V Logic
  3.3V Power      3V3            VCC (OLED & Climate)     Power Rail       3.3V DC
  5.0V Power      5V / VBUS      VIN (NDIR CO2 Sensor)    Power Rail       5.0V DC (USB)
  Common Ground   GND            GND (All Modules)        Ground           0V Ref
  Serial Monitor  Native USB     PC USB Host (COM9)       USB-CDC Native   5V Bus
========================================================================================
```

> [!WARNING]
> **Power Rail Separation:**
> - The NDIR $CO_2$ sensor requires **4.5V to 5.5V DC** on its $V_{IN}$ pin to power the optical infrared heating element (~150 mA peak pulse current). Connect it to the **5V / VBUS** pin of the development board.
> - The communication lines (TX/RX and SDA/SCL) operate at **3.3V TTL**, making them 100% compatible with ESP32-C5 GPIOs.

---

## 🧭 System Architecture

```
                                 +-----------------------------+
                                 |       5V USB Power Supply   |
                                 +--------------+--------------+
                                                |
                                                v
+-------------------------+          +--------------------+          +-----------------------+
|  I2C Graphic OLED       |   I2C    |  Espressif ESP32-C5|   UART   |  NDIR Optical CO2     |
|  SSD1306 (128x64)       |<-------->|  DevKitC-1 N4      |<-------->|  Sensor Module        |
|  Address: 0x3C          | SDA: 8   |  (RISC-V 240 MHz)  | RX: 5    |  9600 bps, 8N1        |
+-------------------------+ SCL: 9   +---------+----------+ TX: 4    +-----------------------+
                                               |
+-------------------------+                    |
|  Precision Climate &    |                    | Native USB CDC (COM9)
|  Barometric Sensor      |<-------------------+ 115200 bps
|  Address: 0x76 / 0x77   | I2C (SDA: 8, SCL: 9)
+-------------------------+                    |
                                               v
                                +------------------------------+
                                |      Bench Monitor GUI       |
                                |     (PyQt6 & pyqtgraph)      |
                                | Live Plots | Stats | Export  |
                                +------------------------------+
```

---

## 🖥️ Desktop GUI Features (Python PyQt6)

The desktop telemetry client (`dashboard_qt.py`) provides a complete monitoring and analysis workspace:

- **60 FPS Real-time Plotting:** Hardware-accelerated curves using `pyqtgraph` for:
  - Carbon Dioxide ($CO_2$ in ppm) with safety threshold lines (800 ppm and 1200 ppm);
  - Temperature (°C) with Dew Point curve overlay;
  - Relative Humidity (% RH);
  - Atmospheric Barometric Pressure (hPa).
- **KPI Metrics Cards:** Instantaneous readout with dynamic badges, min/mean/max stats, and warm-up countdown.
- **Continuous Statistical Computation:** Embedded **pandas** engine computing count, mean, minimum, maximum, and standard deviation in real time.
- **Exporting Tools:**
  - 📥 **CSV Export:** Structured comma/semicolon-separated values with timestamps.
  - 📊 **Excel Export:** Native `.xlsx` spreadsheet workbook formatted with proper data types.
  - 📄 **JSON Export:** Full session array formatted for web or pipeline ingestion.
- **Strictly Real Hardware:** Direct connection to the physical serial port with auto-reconnection and buffer flushing.

---

## 📟 Firmware Architecture & FreeRTOS Concurrency

The ESP32-C5 firmware is modularized into discrete FreeRTOS tasks to guarantee deterministic timing:

1. **`acquisitionTask` (Priority 2, 1 Hz):**
   - Samples climate metrics and $CO_2$ concentration.
   - Computes derived physical values:
     - **Dew Point:** Magnus-Tetens approximation based on temperature and relative humidity.
     - **Hypsometric Altitude:** International barometric formula referencing sea-level pressure ($1013.25\text{ hPa}$).
   - Updates thread-safe shared memory protected by critical sections (`portENTER_CRITICAL`).
2. **`displayTask` (Priority 1, 12.5 FPS / 80 ms):**
   - Renders the 4-page rotating carousel on the OLED screen.
   - Animated visual heartbeat indicator in the top status bar.
3. **`telemetryReporterTask` (Priority 1, 0.5 Hz / 2000 ms):**
   - Transmits structured JSON frames across the native USB-CDC serial channel.
4. **I2C Bus Recovery (`I2CBusManager::recoverBus`):**
   - In the event of a bus lockup caused by noise or hot-plugging, generates 9 manual clock pulses on SCL followed by a STOP condition to restore SDA.

---

## ⚡ Quickstart Guide

### 1. Requirements

- Python 3.10+
- PlatformIO Core 6.1+ (or VSCode with PlatformIO extension)
- Python libraries:
  ```bash
  pip install PyQt6 pyqtgraph pyserial pandas openpyxl numpy
  ```

### 2. Build and Flash Firmware

Using PlatformIO CLI:
```powershell
# Compile firmware
$env:PYTHONIOENCODING="utf-8"; pio run

# Flash to ESP32-C5 on COM9
$env:PYTHONIOENCODING="utf-8"; pio run -t upload --upload-port COM9
```

Or using the bundled Python flasher:
```powershell
python flash_monitor.py --all
```

### 3. Launch Desktop GUI

```powershell
python dashboard_qt.py
```

---

## 📂 Repository Structure

```
bench-monitor/
├── .agents/
│   └── skills/                 # AI Agent Skills (esp32c5, bme280, mhz16, oled)
├── specs/                      # Formal engineering specifications (SPEC_01 to SPEC_06)
├── include/                    # Header files
│   ├── config.h                # Hardware pins, baudrates, and timing configurations
│   ├── i2c_bus.h               # I2C scanner and hardware recovery routine
│   ├── sensor_bme280.h         # Climate sensor driver and calculations
│   ├── sensor_mhz16.h          # NDIR CO2 sensor driver with checksum validation
│   └── display_manager.h       # OLED UI state machine and widgets
├── src/                        # Source implementations
│   ├── i2c_bus.cpp
│   ├── sensor_bme280.cpp
│   ├── sensor_mhz16.cpp
│   ├── display_manager.cpp
│   └── main.cpp                # FreeRTOS setup and task loops
├── dashboard_qt.py             # Desktop telemetry UI in PyQt6 + pyqtgraph
├── flash_monitor.py            # CLI helper to build, flash, and monitor serial output
├── platformio.ini              # PlatformIO project configuration
├── LICENSE                     # GNU General Public License v3.0 (GPLv3)
└── README.md                   # Repository documentation
```

---

## 👤 Author

- **Author:** [xToshiro](https://github.com/xToshiro)
- **Repository:** [https://github.com/xToshiro/bench-monitor](https://github.com/xToshiro/bench-monitor)

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**. See the [LICENSE](LICENSE) file for complete details.
