#pragma once

#include <Arduino.h>

#define PROJECT_NAME        "ESP32-C5 Bancada"
#define FIRMWARE_VERSION    "v1.1.0"
#define SERIAL_BAUD_RATE    115200

#define PIN_I2C_SDA         8
#define PIN_I2C_SCL         9
#define I2C_CLOCK_SPEED     400000L

#define OLED_I2C_ADDR_PRIMARY   0x3C
#define OLED_I2C_ADDR_SECONDARY 0x3D

#define BME280_I2C_ADDR_PRIMARY   0x76
#define BME280_I2C_ADDR_SECONDARY 0x77

#define PIN_MHZ16_RX        5
#define PIN_MHZ16_TX        4
#define MHZ16_BAUD_RATE     9600
#define MHZ16_WARMUP_SEC    180 // Estabilizacao termica da camara NDIR

#define SCREEN_WIDTH        128
#define SCREEN_HEIGHT       64
#define OLED_RESET_PIN      -1
#define SCREEN_CYCLE_TIME_MS 4000

#define SENSOR_SAMPLE_RATE_MS 1000
#define SEA_LEVEL_PRESSURE_HPA 1013.25f

#define MAX_I2C_FAILURES_BEFORE_RESET 3
