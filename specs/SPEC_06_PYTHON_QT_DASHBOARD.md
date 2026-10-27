# SPEC 06: Interface Gráfica Desktop em Python Qt (Dashboard de Bancada)

## 1. Visão Geral
A interface gráfica de bancada **ESP32-C5 Bancada Station** é uma aplicação desktop desenvolvida em **Python 3** utilizando **PyQt6** para a interface de usuário e **pyqtgraph** para renderização de gráficos em tempo real de altíssimo desempenho (60 FPS com aceleração de hardware e baixo consumo de CPU).

Ela se comunica diretamente com a porta serial nativa do ESP32-C5 (**COM9** ou selecionável) a **115200 bps**, decodifica o stream de telemetria JSON emitido pelo firmware, computa estatísticas em tempo real via **pandas** e permite a exportação de dados para **CSV**, **Excel** e **JSON**.

---

## 2. Requisitos Funcionais

1. **Gestão de Conexão Serial:**
   - Varredura e listagem automática de portas seriais disponíveis no Windows;
   - Detecção preferencial da porta **COM9** (`USB VID:PID=303A:1001`);
   - Conexão e desconexão via thread assíncrona desacoplada (`QThread`), sem travar a interface;
   - Operação exclusivamente com hardware físico conectado.

2. **Cards de Métricas em Tempo Real (KPIs):**
   - **$CO_2$ NDIR (ppm):** Valor instantâneo, Mínimo, Máximo, Média e indicador colorido de qualidade do ar (< 700 ppm Excelente, 700-1000 ppm Bom, 1000-1500 ppm Moderado, > 1500 ppm Crítico);
   - **Temperatura (°C):** Valor instantâneo, Mínimo, Máximo e Média;
   - **Umidade Relativa (%):** Valor instantâneo, Mínimo, Máximo, Média e barra de nível;
   - **Pressão e Altitude:** Pressão em hPa, Ponto de Orvalho (°C) e Altitude hipsométrica (m);
   - **Saúde do ESP32-C5:** Uptime, Memória livre (Free Heap em KB), total de amostras e taxa de recepção (Hz).

3. **Gráficos em Tempo Real (`pyqtgraph`):**
   - Gráfico 1: Concentração de $CO_2$ (ppm) com linhas horizontais de referência (800 ppm e 1200 ppm);
   - Gráfico 2: Temperatura (°C) vs. Ponto de Orvalho (°C);
   - Gráfico 3: Umidade Relativa (% RH);
   - Gráfico 4: Pressão Atmosférica (hPa);
   - Zoom, Pan, cursor com coordenadas e seleção de intervalo temporal (1 min, 5 min, 15 min, 1h ou Histórico Completo).

4. **Exportação e Análise de Dados:**
   - Exportação em formato tabular **CSV** estruturado;
   - Exportação em formato **Excel** (`.xlsx`) com colunas tipadas;
   - Exportação em formato **JSON** formatado;
   - Tabela de estatísticas com contagem, média, desvio padrão, mínimo, mediana e máximo.

---

## 3. Arquitetura de Software da Aplicação

```
+--------------------------------------------------------------+
|                     PyQt6 Main Window                        |
|                                                              |
|  +---------------------+   +------------------------------+  |
|  |     Top Toolbar     |   |       KPI Metric Cards       |  |
|  | (COM, Connect, Exp) |   | (Temp, Hum, CO2, Press, Sys) |  |
|  +---------------------+   +------------------------------+  |
|                                                              |
|  +--------------------------------------------------------+  |
|  |               pyqtgraph Plot Grid (4 Canais)           |  |
|  +--------------------------------------------------------+  |
|                                                              |
|  +--------------------------------------------------------+  |
|  |         Tabs: Estatísticas | Tabela Amostras | Log     |  |
|  +--------------------------------------------------------+  |
+------------------------------^-------------------------------+
                               | Qt Signals (JSON Data)
+------------------------------+-------------------------------+
|                      SerialWorker (QThread)                   |
|           pyserial / Buffer / Validador JSON                 |
+------------------------------^-------------------------------+
                               | USB COM9 (115200 bps)
                     [ ESP32-C5 DevKitC-1 ]
```
