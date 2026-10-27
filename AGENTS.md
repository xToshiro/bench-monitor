# Diretrizes de Desenvolvimento e Regras para Agentes (AGENTS.md)

Este documento estabelece as convenções de projeto, arquitetura e instruções operacionais para agentes de IA atuando no repositório **ESP32-C5 Bancada**.

---

## 1. Identificação do Hardware e Conexões
- **Microcontrolador Alvo:** Espressif ESP32-C5 (DevKitC-1 N4), processador RISC-V 32-bit @ 240 MHz.
- **Porta Serial Nativa:** **COM9** (`USB VID:PID=303A:1001`).
- **Barramento I2C Padrão:**
  - **SDA: GPIO 8**
  - **SCL: GPIO 9**
  - Frequência: 400 kHz (Fast Mode).
- **Interface UART1 (Sensor CO2 MH-Z16 NDIR):**
  - **RX: GPIO 5** (Ligado ao pino TX do sensor)
  - **TX: GPIO 4** (Ligado ao pino RX do sensor)
  - Baudrate: 9600 bps (8N1).
- **Periféricos Atuais:**
  1. Display OLED SSD1306 (128x64) no endereço I2C `0x3C` (ou `0x3D`).
  2. Sensor Bosch BME280 (Temp, Umid, Pressão) no endereço I2C `0x76` (ou `0x77`).
  3. Sensor Winsen MH-Z16 v1.2b NDIR (Dióxido de Carbono $CO_2$ em ppm) via UART1.

---

## 2. Padrões de Código e Framework
1. **Framework:** Arduino core sobre ESP-IDF v5.3+ (fork `platform-espressif32` por pioarduino).
2. **Modularidade:**
   - Todo subsistema deve ser dividido em arquivos `.h` (dentro de `include/`) e `.cpp` (dentro de `src/`).
   - Evitar funções monolíticas em `main.cpp`.
3. **Concorrência com FreeRTOS:**
   - Tarefas divididas com períodos fixos via `vTaskDelayUntil()`.
   - Acesso a variáveis compartilhadas protegido por seções críticas (`portENTER_CRITICAL` / `portEXIT_CRITICAL`).
4. **Tratamento de I2C e UART:**
   - O barramento I2C conta com rotinas de auto-recuperação (`I2CBusManager::recoverBus()`) para evitar travamentos caso um sensor sofra ruído ou seja desplugado da bancada.
   - A comunicação UART do MH-Z16 valida obrigatoriamente o cabeçalho (`0xFF 0x86`) e o byte de checksum matemático antes de aceitar qualquer leitura.

---

## 3. Fluxo de Compilação e Gravação no PlatformIO

O binário PlatformIO está localizado em:
`$HOME\.platformio\penv\Scripts\pio.exe`

### Comandos de Terminal no PowerShell:
```powershell
# 1. Compilar
$env:PYTHONIOENCODING="utf-8"; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; & "$HOME\.platformio\penv\Scripts\pio.exe" run

# 2. Gravar na porta COM9
$env:PYTHONIOENCODING="utf-8"; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; & "$HOME\.platformio\penv\Scripts\pio.exe" run -t upload --upload-port COM9

# 3. Monitor Serial
$env:PYTHONIOENCODING="utf-8"; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; & "$HOME\.platformio\penv\Scripts\pio.exe" device monitor -b 115200 --port COM9

# 4. Utilitário Python integrado
python flash_monitor.py --all
```

---

## 4. Estrutura de Especificações (Specs)
Todas as novas adições ao sistema devem receber sua respectiva especificação formal no diretório `specs/`:
- `SPEC_01_SYSTEM_ARCHITECTURE.md`
- `SPEC_02_HARDWARE_PINOUT_I2C.md`
- `SPEC_03_BME280_ACQUISITION.md`
- `SPEC_04_OLED_UI_DASHBOARD.md`
- `SPEC_05_MHZ16_CO2_ACQUISITION.md`
