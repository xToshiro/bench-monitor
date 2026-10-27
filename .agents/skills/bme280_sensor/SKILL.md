---
name: bme280_sensor
description: >-
  Guia de integração, auto-detecção de endereços I2C (0x76/0x77), calibração
  e compensação para o sensor Bosch BME280 no ESP32-C5.
---

# BME280 Sensor Integration Skill

Esta skill descreve o manuseio, parametrização e tratamento de falhas do sensor de pressão, temperatura e umidade BME280 no barramento I2C compartilhado.

## Mapeamento Físico
- **SDA:** GPIO 8 (ESP32-C5)
- **SCL:** GPIO 9 (ESP32-C5)
- **VCC:** 3.3V
- **GND:** GND

## Auto-Detecção de Endereço I2C
O sensor BME280 pode operar em dois endereços de 7 bits dependendo da configuração do pino SDO:
- `0x76`: SDO conectado a GND (padrão na maioria das placas breakout chinesas).
- `0x77`: SDO conectado a VCC / 3.3V (padrão em placas Adafruit).

O código deve sempre tentar o endereço primário e, se falhar, tentar o secundário:
```cpp
if (bme.begin(0x76, &Wire)) {
    Serial.println("[BME280] Inicializado no endereco 0x76");
} else if (bme.begin(0x77, &Wire)) {
    Serial.println("[BME280] Inicializado no endereco 0x77");
} else {
    Serial.println("[BME280] ERRO: Sensor nao detectado!");
}
```

## Configuração Recomendada de Amostragem
Para leitura ambiental contínua em bancada:
- **Modo:** Normal (medição periódica autônoma)
- **Oversampling Temp:** 2x
- **Oversampling Pressão:** 16x
- **Oversampling Umidade:** 1x
- **Filtro IIR:** 16x (elimina ruído de portas abrindo ou correntes de ar)

## Diagnóstico e Solução de Problemas
- **Problema: `bme.begin()` retorna false.**
  1. Verifique se o scanner I2C encontra o dispositivo em `0x76` ou `0x77`.
  2. Verifique se os pinos SDA (GPIO 8) e SCL (GPIO 9) não estão invertidos.
  3. Verifique a presença de resistores pull-up de 4.7 kΩ caso os módulos não possuam integrados.
- **Problema: Leituras congeladas ou NaN.**
  - Execute a rotina de recuperação de barramento I2C e reinicialize a instância do sensor.
