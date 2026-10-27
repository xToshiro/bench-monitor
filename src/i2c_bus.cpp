#include "i2c_bus.h"

bool I2CBusManager::init() {
    Serial.printf("[I2C] Inicializando barramento nos pinos SDA=%d, SCL=%d a %lu Hz...\n", 
                  PIN_I2C_SDA, PIN_I2C_SCL, (unsigned long)I2C_CLOCK_SPEED);
    bool ok = Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, I2C_CLOCK_SPEED);
    if (!ok) {
        Serial.println("[I2C] ERRO ao inicializar o barramento com Wire.begin()! Executando recuperacao de barramento...");
        recoverBus();
        ok = Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, I2C_CLOCK_SPEED);
    }
    return ok;
}

I2CBusScanResult I2CBusManager::scan() {
    I2CBusScanResult result = {0, false, 0, false, 0};
    Serial.println("\n------------------------------------------------");
    Serial.println("[I2C] Iniciando varredura de enderecos I2C (0x01 a 0x7E)...");

    for (uint8_t address = 1; address < 127; address++) {
        Wire.beginTransmission(address);
        uint8_t error = Wire.endTransmission();

        if (error == 0) {
            result.devices_found++;
            Serial.printf("  -> Dispositivo encontrado no endereco 0x%02X", address);

            if (address == OLED_I2C_ADDR_PRIMARY || address == OLED_I2C_ADDR_SECONDARY) {
                result.oled_found = true;
                result.oled_addr = address;
                Serial.print(" [Display OLED SSD1306]");
            } else if (address == BME280_I2C_ADDR_PRIMARY || address == BME280_I2C_ADDR_SECONDARY) {
                result.bme280_found = true;
                result.bme280_addr = address;
                Serial.print(" [Sensor Bosch BME280]");
            }
            Serial.println();
        } else if (error == 4) {
            Serial.printf("  [!] Erro desconhecido no endereco 0x%02X\n", address);
        }
    }

    if (result.devices_found == 0) {
        Serial.println("[I2C] AVISO: Nenhum dispositivo I2C respondeu!");
    } else {
        Serial.printf("[I2C] Varredura concluida: %d dispositivo(s) detectado(s).\n", result.devices_found);
    }
    Serial.println("------------------------------------------------\n");

    return result;
}

void I2CBusManager::recoverBus() {
    Serial.println("[I2C] Executando rotina de clocking para liberar linha SDA (Bus Recovery)...");
    Wire.end();

    pinMode(PIN_I2C_SDA, INPUT_PULLUP);
    pinMode(PIN_I2C_SCL, OUTPUT);

    // Envia 9 pulsos de clock em SCL para forçar o escravo travado a soltar a linha SDA
    for (int i = 0; i < 9; i++) {
        digitalWrite(PIN_I2C_SCL, HIGH);
        delayMicroseconds(5);
        digitalWrite(PIN_I2C_SCL, LOW);
        delayMicroseconds(5);
    }

    // Gera condição de STOP
    pinMode(PIN_I2C_SDA, OUTPUT);
    digitalWrite(PIN_I2C_SDA, LOW);
    delayMicroseconds(5);
    digitalWrite(PIN_I2C_SCL, HIGH);
    delayMicroseconds(5);
    digitalWrite(PIN_I2C_SDA, HIGH);
    delayMicroseconds(5);

    pinMode(PIN_I2C_SDA, INPUT_PULLUP);
    pinMode(PIN_I2C_SCL, INPUT_PULLUP);
    Serial.println("[I2C] Rotina de recuperacao concluida.");
}
