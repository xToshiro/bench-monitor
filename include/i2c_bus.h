#pragma once

#include <Arduino.h>
#include <Wire.h>
#include "config.h"

struct I2CBusScanResult {
    uint8_t devices_found;
    bool oled_found;
    uint8_t oled_addr;
    bool bme280_found;
    uint8_t bme280_addr;
};

class I2CBusManager {
public:
    static bool init();
    static I2CBusScanResult scan();
    static void recoverBus();
};
