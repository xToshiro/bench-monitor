#include "sensor_bme280.h"
#include <cmath>

SensorBME280::SensorBME280() : _connected(false), _address(0), _consecutive_errors(0) {}

bool SensorBME280::begin(uint8_t forced_addr) {
    _connected = false;

    if (forced_addr != 0) {
        if (_bme.begin(forced_addr, &Wire)) {
            _connected = true;
            _address = forced_addr;
        }
    } else {
        if (_bme.begin(BME280_I2C_ADDR_PRIMARY, &Wire)) {
            _connected = true;
            _address = BME280_I2C_ADDR_PRIMARY;
        } else if (_bme.begin(BME280_I2C_ADDR_SECONDARY, &Wire)) {
            _connected = true;
            _address = BME280_I2C_ADDR_SECONDARY;
        }
    }

    if (_connected) {
        Serial.printf("[BME280] Sensor inicializado com SUCESSO no endereco 0x%02X!\n", _address);
        _bme.setSampling(Adafruit_BME280::MODE_NORMAL,
                         Adafruit_BME280::SAMPLING_X2,
                         Adafruit_BME280::SAMPLING_X16,
                         Adafruit_BME280::SAMPLING_X1,
                         Adafruit_BME280::FILTER_X16,
                         Adafruit_BME280::STANDBY_MS_500);
        _consecutive_errors = 0;
        return true;
    }

    Serial.println("[BME280] AVISO: Sensor BME280 nao respondeu nos enderecos 0x76 ou 0x77.");
    return false;
}

bool SensorBME280::read(BME280Readings& out) {
    if (!_connected) {
        if (!begin()) {
            out.valid = false;
            out.error_count = ++_consecutive_errors;
            return false;
        }
    }

    float temp = _bme.readTemperature();
    float hum = _bme.readHumidity();
    float press_pa = _bme.readPressure();

    if (isnan(temp) || isnan(hum) || isnan(press_pa) || press_pa < 30000.0f) {
        _consecutive_errors++;
        out.valid = false;
        out.error_count = _consecutive_errors;
        Serial.printf("[BME280] Falha na leitura (Tentativa %lu com erro)\n", (unsigned long)_consecutive_errors);

        if (_consecutive_errors >= MAX_I2C_FAILURES_BEFORE_RESET) {
            _connected = false;
        }
        return false;
    }

    _consecutive_errors = 0;
    out.valid = true;
    out.temperature = temp;
    out.humidity = hum;
    out.pressure = press_pa / 100.0f;
    out.altitude = calculateAltitude(out.pressure);
    out.dew_point = calculateDewPoint(temp, hum);
    out.i2c_address = _address;
    out.last_read_ms = millis();
    out.error_count = 0;

    return true;
}

float SensorBME280::calculateDewPoint(float temp_c, float humidity_pct) {
    // Equação de Magnus-Tetens
    const float b = 17.27f;
    const float c = 237.7f;
    if (humidity_pct <= 0.0f) humidity_pct = 0.01f;
    float gamma = (b * temp_c) / (c + temp_c) + log(humidity_pct / 100.0f);
    return (c * gamma) / (b - gamma);
}

float SensorBME280::calculateAltitude(float pressure_hpa) {
    // Fórmula barométrica internacional
    return 44330.0f * (1.0f - pow(pressure_hpa / SEA_LEVEL_PRESSURE_HPA, 0.1903f));
}
