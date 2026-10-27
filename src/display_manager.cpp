#include "display_manager.h"

DisplayManager::DisplayManager()
    : _display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET_PIN),
      _initialized(false),
      _address(0),
      _current_screen(SCREEN_CLIMATE),
      _last_screen_switch_ms(0),
      _heartbeat_frame(0) {}

bool DisplayManager::begin(uint8_t forced_addr) {
    _initialized = false;

    if (forced_addr != 0) {
        if (_display.begin(SSD1306_SWITCHCAPVCC, forced_addr)) {
            _initialized = true;
            _address = forced_addr;
        }
    } else {
        if (_display.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_ADDR_PRIMARY)) {
            _initialized = true;
            _address = OLED_I2C_ADDR_PRIMARY;
        } else if (_display.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_ADDR_SECONDARY)) {
            _initialized = true;
            _address = OLED_I2C_ADDR_SECONDARY;
        }
    }

    if (_initialized) {
        Serial.printf("[OLED] Display inicializado com SUCESSO no endereco 0x%02X!\n", _address);
        _display.clearDisplay();
        _display.setTextColor(SSD1306_WHITE);
        _display.display();
        _last_screen_switch_ms = millis();
        return true;
    }

    Serial.println("[OLED] AVISO: Display SSD1306 nao encontrado no barramento I2C.");
    return false;
}

void DisplayManager::showSplashScreen() {
    if (!_initialized) return;

    _display.clearDisplay();
    _display.drawRoundRect(0, 0, 128, 64, 4, SSD1306_WHITE);

    _display.setTextSize(1);
    _display.setTextColor(SSD1306_WHITE);
    _display.setCursor(18, 10);
    _display.print("ESP32-C5 BANCADA");

    _display.setCursor(8, 22);
    _display.print("TELEMETRIA AMBIENTAL");

    _display.setCursor(22, 34);
    _display.print("I2C:8,9  UART:5,4");

    _display.drawRect(20, 48, 88, 6, SSD1306_WHITE);
    for (int w = 0; w <= 84; w += 14) {
        _display.fillRect(22, 50, w, 2, SSD1306_WHITE);
        _display.display();
        delay(50);
    }
    delay(300);
}

void DisplayManager::drawHeader(const char* title, uint8_t page_num) {
    _display.setTextSize(1);
    _display.setTextColor(SSD1306_WHITE);
    _display.setCursor(2, 1);
    _display.printf("[%s]", title);

    _display.setCursor(80, 1);
    _display.printf("P%d/%d", page_num, SCREEN_COUNT);

    _heartbeat_frame = (_heartbeat_frame + 1) % 4;
    int hx = 122;
    int hy = 4;
    if (_heartbeat_frame == 0 || _heartbeat_frame == 2) {
        _display.fillCircle(hx, hy, 2, SSD1306_WHITE);
    } else {
        _display.drawCircle(hx, hy, 2, SSD1306_WHITE);
    }

    _display.drawLine(0, 10, 127, 10, SSD1306_WHITE);
}

void DisplayManager::update(const BME280Readings& bme, const MHZ16Readings& co2) {
    if (!_initialized) return;

    if (millis() - _last_screen_switch_ms >= SCREEN_CYCLE_TIME_MS) {
        nextScreen();
        _last_screen_switch_ms = millis();
    }

    _display.clearDisplay();

    if (!bme.valid && !co2.valid) {
        showSensorOfflineScreen();
        _display.display();
        return;
    }

    switch (_current_screen) {
        case SCREEN_CLIMATE:
            renderScreenClimate(bme);
            break;
        case SCREEN_CO2:
            renderScreenCO2(co2);
            break;
        case SCREEN_BAROMETRY:
            renderScreenBarometry(bme);
            break;
        case SCREEN_SYSTEM:
            renderScreenSystem(bme, co2);
            break;
        default:
            _current_screen = SCREEN_CLIMATE;
            break;
    }

    _display.display();
}

void DisplayManager::nextScreen() {
    _current_screen = (DisplayScreen)((_current_screen + 1) % SCREEN_COUNT);
}

void DisplayManager::renderScreenClimate(const BME280Readings& readings) {
    drawHeader("CLIMA", 1);

    if (!readings.valid) {
        _display.setTextSize(1);
        _display.setCursor(10, 30);
        _display.print("BME280 desconectado");
        return;
    }

    _display.setTextSize(2);
    _display.setCursor(4, 15);
    _display.printf("%.1f C", readings.temperature);
    _display.drawCircle(66, 17, 2, SSD1306_WHITE);

    _display.setTextSize(1);
    _display.setCursor(4, 35);
    _display.printf("Umidade: %.1f %%", readings.humidity);

    _display.setCursor(4, 46);
    _display.printf("Orvalho: %.1f C", readings.dew_point);

    _display.drawRect(4, 56, 120, 6, SSD1306_WHITE);
    float hum_clamped = constrain(readings.humidity, 0.0f, 100.0f);
    int bar_width = (int)((hum_clamped / 100.0f) * 116.0f);
    if (bar_width > 0) {
        _display.fillRect(6, 58, bar_width, 2, SSD1306_WHITE);
    }
}

void DisplayManager::renderScreenCO2(const MHZ16Readings& readings) {
    drawHeader("CO2 NDIR", 2);

    if (!readings.valid) {
        _display.setTextSize(1);
        _display.setCursor(4, 25);
        _display.print("MH-Z16: Sem dados");
        _display.setCursor(4, 40);
        _display.print("Verif. RX=5 TX=4");
        _display.setCursor(4, 52);
        _display.print("Alimentar c/ 5V USB");
        return;
    }

    _display.setTextSize(2);
    _display.setCursor(4, 15);
    _display.printf("%d", readings.co2_ppm);
    _display.setTextSize(1);
    _display.setCursor(76, 21);
    _display.print("ppm");

    _display.setCursor(4, 36);
    if (readings.is_warming_up) {
        _display.printf("Aquecendo (%ds)", readings.warmup_remaining_s);
    } else {
        if (readings.co2_ppm < 700) {
            _display.print("Ar: EXCELENTE");
        } else if (readings.co2_ppm < 1000) {
            _display.print("Ar: BOM / ACEITAVEL");
        } else if (readings.co2_ppm < 1500) {
            _display.print("Ar: MODERADO / VENTILAR");
        } else {
            _display.print("ALERTA: AR CRITICO!");
        }
    }

    _display.drawRect(4, 48, 120, 7, SSD1306_WHITE);
    float norm = ((float)readings.co2_ppm - 400.0f) / 1600.0f;
    norm = constrain(norm, 0.0f, 1.0f);
    int bar_w = (int)(norm * 116.0f);
    if (bar_w > 0) {
        _display.fillRect(6, 50, bar_w, 3, SSD1306_WHITE);
    }
}

void DisplayManager::renderScreenBarometry(const BME280Readings& readings) {
    drawHeader("BAROMETRIA", 3);

    if (!readings.valid) {
        _display.setTextSize(1);
        _display.setCursor(10, 30);
        _display.print("Barometro offline");
        return;
    }

    _display.setTextSize(1);
    _display.setCursor(4, 15);
    _display.print("Pressao:");
    _display.setTextSize(2);
    _display.setCursor(4, 25);
    _display.printf("%.1f", readings.pressure);
    _display.setTextSize(1);
    _display.setCursor(96, 31);
    _display.print("hPa");

    _display.setCursor(4, 45);
    _display.printf("Alt. Est.: %.0f m", readings.altitude);

    _display.setCursor(4, 55);
    _display.printf("I2C: 0x%02X (OK)", readings.i2c_address);
}

void DisplayManager::renderScreenSystem(const BME280Readings& bme, const MHZ16Readings& co2) {
    drawHeader("SISTEMA", 4);

    _display.setTextSize(1);
    _display.setCursor(4, 13);
    _display.print("ESP32-C5 (RISC-V)");

    uint32_t sec = millis() / 1000;
    uint32_t min = sec / 60;
    uint32_t hr = min / 60;
    _display.setCursor(4, 23);
    _display.printf("Uptime: %02lu:%02lu:%02lu", (unsigned long)hr, (unsigned long)(min % 60), (unsigned long)(sec % 60));

    _display.setCursor(4, 33);
    _display.printf("Heap: %lu KB", (unsigned long)(esp_get_free_heap_size() / 1024));

    _display.setCursor(4, 43);
    _display.printf("I2C: SDA:8 SCL:9 %s", bme.valid ? "(OK)" : "(!)");

    _display.setCursor(4, 53);
    _display.printf("UART: RX:5 TX:4 %s", co2.valid ? "(OK)" : "(!)");
}

void DisplayManager::showSensorOfflineScreen() {
    drawHeader("ALERTA", 0);

    _display.drawRoundRect(4, 14, 120, 48, 3, SSD1306_WHITE);

    _display.setTextSize(1);
    _display.setCursor(14, 20);
    _display.print("SENSORES OFFLINE");

    _display.setCursor(8, 34);
    _display.print("Barram. I2C: SDA:8 SCL:9");

    _display.setCursor(8, 48);
    _display.print("Canal UART:  RX:5 TX:4");
}
