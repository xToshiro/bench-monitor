# SPEC 01: Arquitetura do Sistema ESP32-C5 Bancada

## 1. Visão Geral
O projeto **ESP32-C5 Bancada** consiste em uma estação microcontrolada modular de monitoramento ambiental e validação sensorial de bancada, baseada no microcontrolador Espressif **ESP32-C5** (arquitetura RISC-V 32-bit de 240 MHz com Wi-Fi 6 Dual-Band 2.4/5 GHz e Bluetooth 5 LE).

O sistema integra:
- Display OLED I2C (controlador SSD1306, resolução 128x64) para telemetria local em tempo real;
- Barramento I2C compartilhado dedicado para sensores com auto-recuperação de barramento;
- Sensor primário ambiental: **Bosch BME280** (temperatura, umidade relativa do ar e pressão barométrica);
- Arquitetura de software modular sob FreeRTOS (tarefas de aquisição, renderização gráfica e diagnóstico serial).

---

## 2. Diagrama de Blocos do Sistema

```
                      +-----------------------------+
                      |       Alimentação USB       |
                      |          5V / 3.3V          |
                      +--------------+--------------+
                                     |
                                     v
+-------------------+     +---------------------+     +--------------------+
|    Display OLED   |     |      ESP32-C5       |     |   Sensor Bosch     |
|   SSD1306 128x64  |<--->|    DevKitC-1 N4     |<--->|      BME280        |
|  (Endereço 0x3C)  | I2C |   (COM9 / USB-CDC)  | I2C | (Endereço 0x76/77) |
+-------------------+     +----------+----------+     +--------------------+
  SDA: GPIO 8                        |                  SDA: GPIO 8
  SCL: GPIO 9                        |                  SCL: GPIO 9
                                     v
                         +-----------------------+
                         |  Console Serial USB   |
                         | 115200 bps (COM9)     |
                         | JSON Stream / Logs    |
                         +-----------------------+
```

---

## 3. Especificações Técnicas de Hardware

| Parâmetro | Detalhes |
| :--- | :--- |
| **Microcontrolador** | Espressif ESP32-C5 (Single-core RISC-V RV32IMC, até 240 MHz) |
| **Conectividade Sem Fio** | Dual-Band Wi-Fi 6 (2.4 GHz e 5.0 GHz 802.11ax) + Bluetooth 5 (LE) |
| **Memória Flash** | 4 MB Quad-SPI Flash (esp32-c5-devkitc-1) |
| **SRAM Interna** | 320 KB SRAM |
| **Interface Serial / Debug** | USB Serial/JTAG nativo (`ARDUINO_USB_CDC_ON_BOOT=1`) na porta **COM9** |
| **Barramento I2C** | Pinos dedicados: **SDA = GPIO 8**, **SCL = GPIO 9** (Velocidade nominal: 400 kHz) |
| **Nível Lógico de E/S** | 3.3V LVCMOS |

---

## 4. Arquitetura de Software e Concorrência (FreeRTOS)

O firmware é desacoplado em tarefas coordenadas via FreeRTOS para garantir determinismo temporal e isolamento de falhas:

1. **`acquisitionTask` (Prioridade 2, Frequência: 1 Hz):**
   - Coleta periódica das leituras do BME280;
   - Cálculo de grandezas secundárias (ponto de orvalho, altitude barométrica barométrica internacional);
   - Verificação de integridade e watchdogs dos sensores;
   - Atualização da estrutura atômica thread-safe `SystemTelemetryData`.

2. **`displayTask` (Prioridade 1, Frequência: 15–20 Hz):**
   - Atualização gráfica no display SSD1306;
   - Máquina de estados das telas (Carrossel automático / Telas métricas / Diagnóstico);
   - Animação suave de transição de tela e indicadores pulsantes de status do barramento.

3. **`telemetryReporterTask` (Prioridade 1, Frequência: 1 Hz):**
   - Emissão de telemetria estruturada em formato JSON legível na porta USB Serial (115200 bps);
   - Logs de eventos e alertas caso o barramento I2C sofra NACK.

---

## 5. Estrutura de Diretórios do Projeto

```
bancada/
├── .agents/
│   └── skills/
│       ├── esp32c5_bancada/       # Instruções de compilação, flash e monitoramento
│       ├── bme280_sensor/          # Guias de calibração e leitura do BME280
│       └── oled_display/           # Guia de renderização e telas OLED SSD1306
├── specs/
│   ├── SPEC_01_SYSTEM_ARCHITECTURE.md
│   ├── SPEC_02_HARDWARE_PINOUT_I2C.md
│   ├── SPEC_03_BME280_ACQUISITION.md
│   └── SPEC_04_OLED_UI_DASHBOARD.md
├── include/
│   ├── config.h                   # Definições de pinos, taxas e constantes
│   ├── i2c_bus.h                  # Scanner e inicialização robusta do barramento
│   ├── sensor_bme280.h            # Driver e estruturas de dados do BME280
│   └── display_manager.h          # Gerenciador de telas do display OLED
├── src/
│   ├── i2c_bus.cpp
│   ├── sensor_bme280.cpp
│   ├── display_manager.cpp
│   └── main.cpp                   # Ponto de entrada e agendador FreeRTOS
├── libraries/                     # Dependências locais e drivers Adafruit
├── flash_monitor.py               # Utilitário CLI de compilação, upload e monitor COM9
├── platformio.ini                 # Configuração de build PlatformIO
├── README.md
├── TECHNICAL_DOCUMENTATION.md
└── AGENTS.md
```
