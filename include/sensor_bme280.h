#pragma once

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include "config.h"

struct BME280Readings {
    bool valid;
    float temperature;   // Graus Celsius (°C)
    float humidity;      // Umidade Relativa (%)
    float pressure;      // Pressão Atmosférica (hPa)
    float altitude;      // Altitude Barométrica Estimada (m)
    float dew_point;     // Ponto de Orvalho Calculado (°C)
    uint8_t i2c_address; // Endereço I2C em uso (0x76 ou 0x77)
    uint32_t last_read_ms;
    uint32_t error_count;
};

class SensorBME280 {
public:
    SensorBME280();
    bool begin(uint8_t forced_addr = 0);
    bool read(BME280Readings& out);
    bool isConnected() const { return _connected; }
    uint8_t getAddress() const { return _address; }

private:
    Adafruit_BME280 _bme;
    bool _connected;
    uint8_t _address;
    uint32_t _consecutive_errors;

    float calculateDewPoint(float temp_c, float humidity_pct);
    float calculateAltitude(float pressure_hpa);
};
