#pragma once

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "config.h"
#include "sensor_bme280.h"
#include "sensor_mhz16.h"

enum DisplayScreen {
    SCREEN_CLIMATE = 0,    // Temperatura e Umidade com barra gráfica
    SCREEN_CO2 = 1,        // Concentração de CO2 (ppm), qualidade do ar e warmup
    SCREEN_BAROMETRY = 2,  // Pressão atmosférica e altitude
    SCREEN_SYSTEM = 3,     // Diagnóstico ESP32-C5, Heap, Uptime, I2C e UART
    SCREEN_COUNT = 4
};

class DisplayManager {
public:
    DisplayManager();
    bool begin(uint8_t forced_addr = 0);
    void update(const BME280Readings& bme, const MHZ16Readings& co2);
    void showSplashScreen();
    void showSensorOfflineScreen();
    void nextScreen();

private:
    Adafruit_SSD1306 _display;
    bool _initialized;
    uint8_t _address;
    DisplayScreen _current_screen;
    uint32_t _last_screen_switch_ms;
    uint8_t _heartbeat_frame;

    void drawHeader(const char* title, uint8_t page_num);
    void renderScreenClimate(const BME280Readings& readings);
    void renderScreenCO2(const MHZ16Readings& readings);
    void renderScreenBarometry(const BME280Readings& readings);
    void renderScreenSystem(const BME280Readings& bme, const MHZ16Readings& co2);
};
