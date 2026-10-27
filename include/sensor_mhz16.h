#pragma once

#include <Arduino.h>
#include "config.h"

struct MHZ16Readings {
    bool valid;
    uint16_t co2_ppm;
    bool is_warming_up;
    uint16_t warmup_remaining_s;
    uint32_t last_read_ms;
    uint32_t error_count;
};

class SensorMHZ16 {
public:
    SensorMHZ16();
    bool begin(int rxPin = PIN_MHZ16_RX, int txPin = PIN_MHZ16_TX);
    bool read(MHZ16Readings& out);
    bool isConnected() const { return _connected; }

private:
    HardwareSerial _serial;
    bool _connected;
    uint32_t _boot_time_ms;
    uint32_t _consecutive_errors;

    uint8_t calculateChecksum(const uint8_t* packet);
};
