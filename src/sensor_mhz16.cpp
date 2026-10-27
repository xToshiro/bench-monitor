#include "sensor_mhz16.h"

SensorMHZ16::SensorMHZ16()
    : _serial(1), _connected(false), _boot_time_ms(0), _consecutive_errors(0) {}

bool SensorMHZ16::begin(int rxPin, int txPin) {
    Serial.printf("[MH-Z16] Inicializando UART1 para sensor NDIR de CO2 (RX=GPIO %d, TX=GPIO %d a %d bps)...\n",
                  rxPin, txPin, MHZ16_BAUD_RATE);
    _serial.begin(MHZ16_BAUD_RATE, SERIAL_8N1, rxPin, txPin);
    _boot_time_ms = millis();
    _connected = true;
    _consecutive_errors = 0;
    return true;
}

uint8_t SensorMHZ16::calculateChecksum(const uint8_t* packet) {
    uint8_t sum = 0;
    for (int i = 1; i < 8; i++) {
        sum += packet[i];
    }
    return (uint8_t)((0xFF - sum) + 1);
}

bool SensorMHZ16::read(MHZ16Readings& out) {
    if (!_connected) {
        out.valid = false;
        out.error_count = ++_consecutive_errors;
        return false;
    }

    while (_serial.available() > 0) {
        _serial.read();
    }

    const uint8_t cmd[9] = {0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79};
    _serial.write(cmd, 9);
    _serial.flush();

    uint32_t start_wait = millis();
    while (_serial.available() < 9 && (millis() - start_wait < 250)) {
        delay(5);
    }

    if (_serial.available() < 9) {
        _consecutive_errors++;
        out.valid = false;
        out.error_count = _consecutive_errors;
        return false;
    }

    uint8_t response[9];
    _serial.readBytes(response, 9);

    if (response[0] != 0xFF || response[1] != 0x86) {
        _consecutive_errors++;
        out.valid = false;
        out.error_count = _consecutive_errors;
        Serial.printf("[MH-Z16] Cabecalho invalido: 0x%02X 0x%02X\n", response[0], response[1]);
        return false;
    }

    uint8_t expected_crc = calculateChecksum(response);
    if (response[8] != expected_crc) {
        _consecutive_errors++;
        out.valid = false;
        out.error_count = _consecutive_errors;
        Serial.printf("[MH-Z16] Erro de checksum: recebido 0x%02X, esperado 0x%02X\n", response[8], expected_crc);
        return false;
    }

    uint16_t ppm = ((uint16_t)response[2] << 8) | response[3];
    if (ppm > 10000) {
        _consecutive_errors++;
        out.valid = false;
        out.error_count = _consecutive_errors;
        return false;
    }

    _consecutive_errors = 0;
    out.valid = true;
    out.co2_ppm = ppm;
    out.last_read_ms = millis();
    out.error_count = 0;

    uint32_t elapsed_s = (millis() - _boot_time_ms) / 1000;
    if (elapsed_s < MHZ16_WARMUP_SEC) {
        out.is_warming_up = true;
        out.warmup_remaining_s = (uint16_t)(MHZ16_WARMUP_SEC - elapsed_s);
    } else {
        out.is_warming_up = false;
        out.warmup_remaining_s = 0;
    }

    return true;
}
