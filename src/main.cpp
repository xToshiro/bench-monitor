#include <Arduino.h>
#include "config.h"
#include "i2c_bus.h"
#include "sensor_bme280.h"
#include "sensor_mhz16.h"
#include "display_manager.h"

SensorBME280 sensorBME;
SensorMHZ16  sensorCO2;
DisplayManager displayMgr;

static BME280Readings sharedBMEReadings;
static MHZ16Readings  sharedCO2Readings;
static portMUX_TYPE   dataMutex = portMUX_INITIALIZER_UNLOCKED;

void acquisitionTask(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(SENSOR_SAMPLE_RATE_MS);
    uint32_t cycle_count = 0;

    for (;;) {
        cycle_count++;

        BME280Readings tempBME;
        sensorBME.read(tempBME);

        MHZ16Readings tempCO2;
        static MHZ16Readings lastValidCO2;
        if (cycle_count % 2 == 0) {
            if (sensorCO2.read(tempCO2)) {
                lastValidCO2 = tempCO2;
            } else {
                tempCO2 = lastValidCO2;
            }
        } else {
            tempCO2 = lastValidCO2;
        }

        portENTER_CRITICAL(&dataMutex);
        sharedBMEReadings = tempBME;
        sharedCO2Readings = tempCO2;
        portEXIT_CRITICAL(&dataMutex);

        vTaskDelayUntil(&xLastWakeTime, xFrequency);
    }
}

void displayTask(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(80);

    for (;;) {
        BME280Readings currentBME;
        MHZ16Readings  currentCO2;

        portENTER_CRITICAL(&dataMutex);
        currentBME = sharedBMEReadings;
        currentCO2 = sharedCO2Readings;
        portEXIT_CRITICAL(&dataMutex);

        displayMgr.update(currentBME, currentCO2);

        vTaskDelayUntil(&xLastWakeTime, xFrequency);
    }
}

void telemetryReporterTask(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(2000);

    for (;;) {
        BME280Readings bme;
        MHZ16Readings  co2;

        portENTER_CRITICAL(&dataMutex);
        bme = sharedBMEReadings;
        co2 = sharedCO2Readings;
        portEXIT_CRITICAL(&dataMutex);

        Serial.printf("{\"device\":\"ESP32-C5\",\"uptime_s\":%lu", (unsigned long)(millis() / 1000));

        if (bme.valid) {
            Serial.printf(",\"temp_c\":%.2f,\"hum_pct\":%.2f,\"press_hpa\":%.2f,\"alt_m\":%.1f,\"dew_c\":%.2f",
                          bme.temperature, bme.humidity, bme.pressure, bme.altitude, bme.dew_point);
        } else {
            Serial.print(",\"bme_status\":\"OFFLINE\"");
        }

        if (co2.valid) {
            Serial.printf(",\"co2_ppm\":%u,\"co2_warmup\":%s,\"co2_warmup_rem_s\":%u",
                          co2.co2_ppm,
                          co2.is_warming_up ? "true" : "false",
                          co2.warmup_remaining_s);
        } else {
            Serial.print(",\"co2_status\":\"OFFLINE\"");
        }

        Serial.printf(",\"heap_free\":%lu}\n", (unsigned long)esp_get_free_heap_size());

        vTaskDelayUntil(&xLastWakeTime, xFrequency);
    }
}

void setup() {
    Serial.begin(SERIAL_BAUD_RATE);
    delay(1500); // Aguarda estabilizacao do canal USB-CDC nativo

    Serial.println("\n==================================================");
    Serial.printf("   %s - %s\n", PROJECT_NAME, FIRMWARE_VERSION);
    Serial.println("   SoC: Espressif ESP32-C5 (RISC-V 240MHz)");
    Serial.printf("   I2C Pinout : SDA=GPIO %d, SCL=GPIO %d (BME280 + OLED)\n", PIN_I2C_SDA, PIN_I2C_SCL);
    Serial.printf("   UART Pinout: RX=GPIO %d, TX=GPIO %d (MH-Z16 NDIR CO2)\n", PIN_MHZ16_RX, PIN_MHZ16_TX);
    Serial.println("==================================================");

    if (!I2CBusManager::init()) {
        Serial.println("[MAIN] AVISO CRITICO: Falha ao inicializar o barramento I2C!");
    }
    I2CBusScanResult scan = I2CBusManager::scan();

    if (displayMgr.begin(scan.oled_found ? scan.oled_addr : 0)) {
        displayMgr.showSplashScreen();
    } else {
        Serial.println("[MAIN] AVISO: Display OLED nao detectado.");
    }

    if (!sensorBME.begin(scan.bme280_found ? scan.bme280_addr : 0)) {
        Serial.println("[MAIN] AVISO: Sensor BME280 nao inicializado. Tentara reconectar em runtime.");
    }

    sensorCO2.begin(PIN_MHZ16_RX, PIN_MHZ16_TX);

    sharedBMEReadings.valid = false;
    sharedBMEReadings.error_count = 0;
    sharedCO2Readings.valid = false;
    sharedCO2Readings.error_count = 0;
    sharedCO2Readings.is_warming_up = true;
    sharedCO2Readings.warmup_remaining_s = MHZ16_WARMUP_SEC;

    xTaskCreate(
        acquisitionTask,
        "AcquisitionTask",
        4096,
        NULL,
        2,
        NULL
    );

    xTaskCreate(
        displayTask,
        "DisplayTask",
        4096,
        NULL,
        1,
        NULL
    );

    xTaskCreate(
        telemetryReporterTask,
        "TelemetryTask",
        3072,
        NULL,
        1,
        NULL
    );

    Serial.println("[MAIN] Sistema operacional FreeRTOS em execucao!");
    Serial.println("[MAIN] Monitorando sensores...\n");
}

void loop() {
    vTaskDelay(pdMS_TO_TICKS(1000));
}
