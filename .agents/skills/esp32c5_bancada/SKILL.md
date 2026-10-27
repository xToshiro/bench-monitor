---
name: esp32c5_bancada
description: >-
  Fluxos operacionais de desenvolvimento, compilação, gravação e monitoramento
  serial para o microcontrolador ESP32-C5 (RISC-V) na porta COM9 usando PlatformIO.
---

# ESP32-C5 Bancada Development Skill

Esta skill descreve o fluxo de trabalho para desenvolver, compilar e gravar firmware na placa de desenvolvimento ESP32-C5 conectada à bancada de testes.

## Localização das Ferramentas
O PlatformIO Core está instalado localmente no ambiente do usuário em:
`$HOME\.platformio\penv\Scripts\pio.exe`

## Comandos Operacionais no PowerShell

### 1. Compilar Firmware
```powershell
$env:PYTHONIOENCODING="utf-8"; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; & "$HOME\.platformio\penv\Scripts\pio.exe" run
```

### 2. Gravar Firmware via USB (COM9)
```powershell
$env:PYTHONIOENCODING="utf-8"; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; & "$HOME\.platformio\penv\Scripts\pio.exe" run -t upload --upload-port COM9
```

### 3. Abrir Monitor Serial (COM9 a 115200 bps)
```powershell
$env:PYTHONIOENCODING="utf-8"; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; & "$HOME\.platformio\penv\Scripts\pio.exe" device monitor -b 115200 --port COM9
```

### 4. Compilar e Gravar em Comando Único
```powershell
$env:PYTHONIOENCODING="utf-8"; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; & "$HOME\.platformio\penv\Scripts\pio.exe" run -t upload --upload-port COM9
```

---

## Particularidades do ESP32-C5

1. **Porta USB Serial/JTAG Nativa:**
   O ESP32-C5 utiliza o controlador USB interno (`303A:1001`). As flags `ARDUINO_USB_MODE=1` e `ARDUINO_USB_CDC_ON_BOOT=1` devem estar sempre presentes no `platformio.ini` para que `Serial.print()` envie dados imediatamente ao canal USB.
2. **Matriz de GPIOs e Barramento I2C:**
   - **SDA: GPIO 8**
   - **SCL: GPIO 9**
   - Ao inicializar o barramento com a biblioteca Wire, sempre utilizar explicitamente:
     ```cpp
     Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
     ```
3. **Reset Suave via DTR/RTS:**
   Caso a placa não responda ao monitor serial após a gravação, pulsar as linhas DTR/RTS para reiniciar o microcontrolador em modo de execução normal.
