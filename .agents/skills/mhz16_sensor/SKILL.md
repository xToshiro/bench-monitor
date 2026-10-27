---
name: mhz16_sensor
description: >-
  Guia de integração do sensor NDIR de CO2 Winsen MH-Z16 (v1.2b) via UART
  (GPIO 5 RX, GPIO 4 TX) no ESP32-C5 com validação de checksum e temporização de warm-up.
---

# Winsen MH-Z16 NDIR CO2 Sensor Skill

Esta skill descreve o protocolo, pinagem e práticas de engenharia para aquisição contínua do sensor óptico de $CO_2$ MH-Z16 no ESP32-C5.

## Pinagem no ESP32-C5
- **Sensor TX** -> **ESP32 GPIO 5** (RX da UART1)
- **Sensor RX** -> **ESP32 GPIO 4** (TX da UART1)
- **Sensor VIN** -> **Pino 5V / VBUS** (Alimentação 5V DC necessária)
- **Sensor GND** -> **GND**

## Inicialização da Porta Serial (HardwareSerial)
```cpp
HardwareSerial mhzSerial(1);

void init_mhz16() {
    mhzSerial.begin(9600, SERIAL_8N1, 5, 4); // (baud, config, rxPin, txPin)
}
```

## Envio e Validação do Telegrama
```cpp
const uint8_t cmd_read[9] = {0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79};

uint8_t calculate_checksum(const uint8_t* packet) {
    uint8_t sum = 0;
    for (int i = 1; i < 8; i++) {
        sum += packet[i];
    }
    return (0xFF - sum) + 1;
}
```

## Cuidados Operacionais
1. **Período de Aquecimento:** O sensor necessita de 180 segundos pós-boot para atingir precisão nominal.
2. **Taxa de Consulta:** Consultar o sensor a cada 2 ou 3 segundos. Consultas em frequências muito altas (> 5 Hz) não aumentam a taxa de resposta da câmara óptica ($T_{90} \approx 30\text{ s}$).
3. **Consumo de Pico:** Certifique-se de que a porta USB forneça corrente suficiente para os pulsos da lâmpada IR (~150 mA).
