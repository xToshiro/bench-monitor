# SPEC 02: Hardware Pinout, Barramento I2C e Conectividade

## 1. Mapeamento de Pinos (Pinout)

O ESP32-C5 possui matriz de comutação flexível de GPIOs (GPIO Matrix). Os pinos a seguir foram definidos para operação na bancada de testes:

| Sinal / Linha | GPIO ESP32-C5 | Conexão no Módulo | Observações |
| :--- | :--- | :--- | :--- |
| **I2C SDA** | **GPIO 8** | Pino SDA (OLED + BME280) | Barramento de dados bidirecional com pull-up de 4.7 kΩ |
| **I2C SCL** | **GPIO 9** | Pino SCL (OLED + BME280) | Barramento de relógio síncrono com pull-up de 4.7 kΩ |
| **VCC 3.3V** | **3V3** | VCC / VIN (OLED + BME280) | Alimentação regulada 3.3V da placa de desenvolvimento |
| **GND** | **GND** | GND comum | Referência de aterramento comum |
| **USB D+ / D-**| **GPIO 13 / 14**| Conector USB Tipo-C nativo | Porta serial virtual COM9 (`USB CDC/JTAG`) |

---

## 2. Mapa de Endereços I2C (7-bit Address Map)

| Endereço Hex | Dispositivo | Função | Observação |
| :--- | :--- | :--- | :--- |
| `0x3C` | Display OLED SSD1306 | Tela gráfica 128x64 | Endereço primário padrão |
| `0x3D` | Display OLED SSD1306 (Alt) | Tela gráfica secundária | Configurado se pino DC/SA0 estiver em VCC |
| `0x76` | Sensor Bosch BME280 | Temp / Umid / Pressão | Endereço padrão na maioria dos módulos (SDO=GND) |
| `0x77` | Sensor Bosch BME280 (Alt) | Temp / Umid / Pressão | Endereço quando pino SDO está em 3.3V |
| `0x08`–`0x68` | *Reservado expansão* | Sensores futuros | Ex: SGP30 (0x58), MICS-6814 / ADC, RTC DS3231 (0x68) |

---

## 3. Topologia Elétrica do Barramento I2C

```
      ESP32-C5 DevKitC-1
     +------------------+
     |                  |           +3.3V
     |                  |             |
     |                  |           [4.7k] [4.7k]  (Pull-ups)
     |                  |             |      |
     |     GPIO 8 (SDA) +-------------+------+---------+ (SDA)
     |                  |                    |         |
     |     GPIO 9 (SCL) +--------------------+---------+ (SCL)
     |                  |                              |
     |              GND +------------------------------+ (GND Comum)
     +------------------+                              |
                                                       |
                  +-----------------------+            |
                  |     Display OLED      |            |
                  |     SSD1306 128x64    |<-----------+
                  |    (Endereço 0x3C)    |
                  +-----------------------+
                                                       |
                  +-----------------------+            |
                  |     Sensor Bosch      |            |
                  |        BME280         |<-----------+
                  |    (Endereço 0x76)    |
                  +-----------------------+
```

### Requisitos Elétricos:
1. **Pull-Up Resistors:** Se os módulos conectados não possuírem resistores pull-up internos ativados, garanta resistores de 4.7 kΩ conectados de SDA e SCL até a linha de 3.3V.
2. **Frequência de Operação (Clock Speed):** Padrão em **400 kHz** (Fast Mode). Se a fiação tiver comprimento superior a 25 cm com alta capacitância parasita, o firmware permite degradar para **100 kHz** (Standard Mode).
3. **Rotina de Recuperação de Linha Travada (I2C Bus Recovery):** Caso um dispositivo escravo mantenha a linha SDA em nível baixo (travamento pós-reset), a rotina de boot do firmware gera até 9 pulsos de clock em SCL até que o escravo libere o barramento (enviando uma condição STOP).

---

## 4. Porta de Comunicação Serial (COM9)

- O chip ESP32-C5 utiliza o controlador USB Serial/JTAG integrado no silício.
- Quando conectado via USB, o sistema operacional Windows atribui a porta **COM9** (`USB VID:PID=303A:1001`).
- Para garantir que a saída `Serial.printf()` seja encaminhada corretamente para o canal USB nativo desde os primeiros milissegundos pós-boot, as seguintes flags são mandatárias no `platformio.ini`:
  ```ini
  build_flags =
      -D ARDUINO_USB_MODE=1
      -D ARDUINO_USB_CDC_ON_BOOT=1
  ```
