---
name: oled_display
description: >-
  Guia de desenvolvimento de interfaces gráficas para display OLED SSD1306 (128x64)
  via barramento I2C com Adafruit GFX e Adafruit SSD1306 no ESP32-C5.
---

# OLED SSD1306 Display Skill

Esta skill descreve as melhores práticas de renderização gráfica, arquitetura de buffers e micro-interações visuais para displays OLED monocromáticos 128x64 conectados ao ESP32-C5.

## Pinagem e Conexão
- **Controlador:** SSD1306
- **Resolução:** 128x64 pixels
- **Endereço I2C:** `0x3C` (padrão) ou `0x3D`
- **SDA:** GPIO 8
- **SCL:** GPIO 9

## Inicialização Padrão
```cpp
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1 // Compartilha reset com ESP32

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

bool init_display() {
    if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3D)) {
            return false;
        }
    }
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.display();
    return true;
}
```

## Práticas de Renderização
1. **Evitar Flickering (Cintilação):** Nunca limpe e renderize a tela diretamente sem um ciclo completo no buffer em memória. Sempre desenhe tudo no frame buffer e faça apenas uma chamada a `display.display()` no final de cada quadro.
2. **Ciclo de Atualização:** Renderizar o display a ~15 Hz ou 20 Hz é suficiente para animações fluidas e não satura o barramento I2C compartilhado com o BME280.
3. **Barra de Status Padronizada:** Manter os primeiros 11 pixels verticais reservados para o status do sistema (nome do dispositivo, indicador I2C, número da tela e batimento cardíaco).
4. **Animação de Ícones:** Indicadores pulsantes (círculos concêntricos preenchidos e vazados) informam visualmente ao operador na bancada que o loop de firmware está ativo.
