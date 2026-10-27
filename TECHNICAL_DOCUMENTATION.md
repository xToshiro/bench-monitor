# Documentação Técnica: Bancada de Testes ESP32-C5

## 1. Visão Geral da Arquitetura de Hardware

A Bancada de Testes foi projetada em torno do microcontrolador **ESP32-C5 (DevKitC-1 N4)**, integrando um barramento I2C compartilhado para visualização local (display OLED SSD1306) e telemetria climática (sensor Bosch BME280), em conjunto com uma interface UART1 assíncrona dedicada ao sensor óptico NDIR de $CO_2$ (Winsen MH-Z16 v1.2b) e uma estação supervisória desktop desenvolvida em Python Qt.

### 1.1. Pinagem Operacional

```
=============================================================================
  Sinal        Pino ESP32-C5     Destino Físico                Protocolo
=============================================================================
  I2C SDA      GPIO 8            Pino SDA do OLED & BME280     I2C (400 kHz)
  I2C SCL      GPIO 9            Pino SCL do OLED & BME280     I2C (400 kHz)
  UART RX      GPIO 5            Pino TX do Sensor MH-Z16      UART1 (9600 bps)
  UART TX      GPIO 4            Pino RX do Sensor MH-Z16      UART1 (9600 bps)
  VCC 3.3V     3V3               VCC / VIN do OLED e BME280    Alimentação 3.3V
  VCC 5.0V     5V / VBUS         Pino 5 (VIN) do MH-Z16        Alimentação 5V USB
  GND          GND               GND Comum                     Aterramento
  USB Serial   Nativo            COM9 (115200 bps)             USB CDC Nativo
=============================================================================
```

---

## 2. Subsistemas de Software do Microcontrolador

### 2.1. Gerenciador de Barramento I2C (`include/i2c_bus.h` e `src/i2c_bus.cpp`)
- Configurado a **400 kHz** nos pinos 8 (SDA) e 9 (SCL).
- Possui rotina de **I2C Bus Recovery**: se o barramento travar em nível lógico baixo, emite 9 ciclos de clock seguidos por condição STOP.
- Auto-detecção de endereços no boot (OLED em `0x3C`/`0x3D` e BME280 em `0x76`/`0x77`).

### 2.2. Driver do Sensor Bosch BME280 (`include/sensor_bme280.h` e `src/sensor_bme280.cpp`)
- Filtro IIR com coeficiente de 16x e amostragem contínua (Normal Mode).
- Cálculo em tempo real:
  - **Altitude Barométrica:** $44330 \cdot (1 - (P / 1013.25)^{0.1903})$ metros.
  - **Ponto de Orvalho:** Equação de Magnus-Tetens baseada em temperatura e umidade relativa.
- Watchdog de reconexão automática em caso de desconexão momentânea.

### 2.3. Driver do Sensor de CO2 MH-Z16 NDIR (`include/sensor_mhz16.h` e `src/sensor_mhz16.cpp`)
- Comunicação via UART1 nos pinos RX: GPIO 5 e TX: GPIO 4 a 9600 bps.
- Envio cíclico do comando de leitura `0x86` (`0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79`).
- Validação matemática de integridade via checksum:
  $$\text{Checksum} = 0xFF - \left(\sum_{i=1}^{7} \text{Byte}[i] \ \& \ 0xFF\right) + 0x01$$
- Cálculo da concentração em ppm: $\text{ppm} = (\text{Byte}[2] \times 256) + \text{Byte}[3]$.
- Controle de período de aquecimento térmico (*warm-up*) de 180 segundos.

### 2.4. Interface Gráfica OLED SSD1306 (`include/display_manager.h` e `src/display_manager.cpp`)
- Dashboard com 4 páginas em carrossel contínuo (troca a cada 4 segundos):
  1. **Clima:** Temperatura (°C), Umidade (%) e barra de conforto.
  2. **CO2 NDIR:** Leitura em ppm com destaque, status de qualidade do ar e contagem regressiva de aquecimento.
  3. **Barometria:** Pressão atmosférica (hPa) e altitude estimada (m).
  4. **Diagnóstico:** Uptime formatado, memória livre da pilha (Free Heap) e integridade dos barramentos I2C e UART.

### 2.5. Concorrência FreeRTOS (`src/main.cpp`)
- **`acquisitionTask` (Prioridade 2, Período 1000 ms):** Amostra BME280 a 1 Hz e MH-Z16 a 0.5 Hz.
- **`displayTask` (Prioridade 1, Período 80 ms):** Renderização gráfica suave a ~12.5 FPS.
- **`telemetryReporterTask` (Prioridade 1, Período 2000 ms):** Transmissão serial em formato JSON unificado contendo métricas de clima e $CO_2$.

---

## 3. Estação de Telemetria Desktop (`dashboard_qt.py`)

A aplicação desktop fornece uma suíte de supervisão e análise para o operador de bancada:
- **Tecnologias:** Python 3, PyQt6, pyqtgraph, pandas, numpy, pyserial, openpyxl.
- **Thread Assíncrona (`SerialWorker`):** Processa dados da porta serial de forma desacoplada da interface gráfica, garantindo 60 FPS contínuos sem bloqueio.
- **Cards KPI com Indicadores:**
  - $CO_2$ com classificação colorida (Verde < 700 ppm, Amarelo < 1000 ppm, Laranja < 1500 ppm, Vermelho $\ge$ 1500 ppm);
  - Temperatura com indicação do ponto de orvalho;
  - Umidade com badge de conforto higrométrico;
  - Pressão e altitude barométrica hipsométrica;
  - Saúde do ESP32-C5 (uptime, heap, amostras).
- **Gráficos em Tempo Real (pyqtgraph):**
  - Gráfico 1: $CO_2$ NDIR com linhas de limiar (800 ppm e 1200 ppm);
  - Gráfico 2: Temperatura e Ponto de Orvalho sobrepostos;
  - Gráfico 3: Umidade Relativa do Ar;
  - Gráfico 4: Pressão Atmosférica.
- **Estatísticas e Exportação:**
  - Tabela com contagem, valor atual, média, mínimo, máximo e desvio padrão calculados em tempo real;
  - Exportação direta com um clique para **CSV**, **Excel (.xlsx)** e **JSON**.
- **Operação Exclusiva em Hardware Real:** Conexão direta aos dados reais da porta COM do ESP32-C5.

---

## 4. Instruções de Execução

```powershell
# 1. Compilar e gravar no ESP32-C5:
python flash_monitor.py --all

# 2. Executar o Dashboard Desktop Python Qt:
python dashboard_qt.py
```
