#pragma once

#include <Arduino.h>

// ==============================================================================
// Identificação e Metadados do Projeto
// ==============================================================================
#define PROJECT_NAME        "ESP32-C5 Bancada"
#define FIRMWARE_VERSION    "v1.1.0"
#define SERIAL_BAUD_RATE    115200

// ==============================================================================
// Configurações do Barramento I2C (Display OLED + BME280)
// ==============================================================================
// Conforme especificação de hardware da bancada:
// SCL = GPIO 9, SDA = GPIO 8
#define PIN_I2C_SDA         8
#define PIN_I2C_SCL         9
#define I2C_CLOCK_SPEED     400000L   // 400 kHz (Fast Mode)

// Endereços I2C Típicos
#define OLED_I2C_ADDR_PRIMARY   0x3C
#define OLED_I2C_ADDR_SECONDARY 0x3D

#define BME280_I2C_ADDR_PRIMARY   0x76
#define BME280_I2C_ADDR_SECONDARY 0x77

// ==============================================================================
// Configurações da UART do Sensor de CO2 MH-Z16 (NDIR)
// ==============================================================================
// Conforme ligação na bancada:
// Sensor TX -> ESP32 GPIO 5 (RX)
// Sensor RX -> ESP32 GPIO 4 (TX)
#define PIN_MHZ16_RX        5
#define PIN_MHZ16_TX        4
#define MHZ16_BAUD_RATE     9600
#define MHZ16_WARMUP_SEC    180       // 3 minutos de pré-aquecimento térmico

// ==============================================================================
// Configurações do Display OLED SSD1306
// ==============================================================================
#define SCREEN_WIDTH        128
#define SCREEN_HEIGHT       64
#define OLED_RESET_PIN      -1        // Sem pino de reset dedicado (compartilhado)
#define SCREEN_CYCLE_TIME_MS 4000     // Rotação automática de telas a cada 4 segundos

// ==============================================================================
// Configurações de Amostragem dos Sensores
// ==============================================================================
#define SENSOR_SAMPLE_RATE_MS 1000    // Aquisição a cada 1 segundo (1 Hz)
#define SEA_LEVEL_PRESSURE_HPA 1013.25f // Pressão padrão ao nível do mar para cálculo de altitude

// ==============================================================================
// Parâmetros de Watchdog e Recuperação de Barramento
// ==============================================================================
#define MAX_I2C_FAILURES_BEFORE_RESET 3
