# SPEC 05: Aquisição de Dados do Sensor NDIR de CO2 MH-Z16 (v1.2b)

## 1. Visão Geral
O **Winsen MH-Z16 (módulo v1.2b)** é um transdutor óptico de alta sensibilidade para Dióxido de Carbono ($CO_2$) baseado no princípio de Infravermelho Não Dispersivo (**NDIR**). Ele se comunica com o microcontrolador ESP32-C5 através de uma interface serial UART assíncrona dedicada.

---

## 2. Pinagem e Conexão de Hardware

| Linha MH-Z16 | Função no Sensor | Conexão ESP32-C5 | Papel no ESP32-C5 |
| :--- | :--- | :--- | :--- |
| **Pino 6 (TX)** | Saída de dados serial (3.3V) | **GPIO 5** | Entrada **RX** da UART1 |
| **Pino 7 (RX)** | Entrada de dados serial (3.3V) | **GPIO 4** | Saída **TX** da UART1 |
| **Pino 5 (VIN)**| Alimentação DC (4.5V a 5.5V) | **5V / VBUS** | Linha de 5V da USB (Pico ~150 mA) |
| **Pino 4 (GND)**| Referência comum | **GND** | Aterramento comum |

> [!IMPORTANT]
> A ligação dos pinos de dados é cruzada:
> - O pino **TX** do sensor transmite dados para a GPIO **5** (RX do ESP32-C5).
> - O pino **RX** do sensor recebe comandos da GPIO **4** (TX do ESP32-C5).

---

## 3. Protocolo de Comunicação UART

- **Baud Rate:** 9600 bps
- **Formato:** 8 bits de dados, sem paridade, 1 stop bit (8N1)
- **Timeouts:** Leitura de resposta em até 1000 ms.

### 3.1. Telegrama de Comando (ESP32 -> MH-Z16)
Para solicitar a concentração atual de $CO_2$, o ESP32-C5 envia a sequência de 9 bytes:
```
0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x79
```

### 3.2. Telegrama de Resposta (MH-Z16 -> ESP32)
O sensor responde com um pacote estruturado de 9 bytes:

| Byte | Nome | Valor / Descrição |
| :--- | :--- | :--- |
| **0** | Start Byte | `0xFF` |
| **1** | Command | `0x86` (Eco do comando) |
| **2** | Concentration High | Byte mais significativo ($HIGH$) |
| **3** | Concentration Low | Byte menos significativo ($LOW$) |
| **4..7**| Reservado | Informações internas de calibração / temperatura |
| **8** | Checksum | Byte de validação matemática |

### 3.3. Algoritmo de Validação de Checksum
$$\text{Checksum} = 0xFF - \left(\sum_{i=1}^{7} \text{Byte}[i] \ \& \ 0xFF\right) + 0x01$$

### 3.4. Cálculo da Concentração
$$\text{CO}_2\ (\text{ppm}) = (\text{HIGH} \times 256) + \text{LOW}$$

---

## 4. Classificação dos Níveis de CO2 (Qualidade do Ar Interior)

| Faixa (ppm) | Classificação | Ação Recomendada |
| :--- | :--- | :--- |
| **< 600 ppm** | Excelente / Ar Limpo | Nível similar ao ar externo |
| **600 a 1000 ppm** | Bom / Aceitável | Ventilação padrão adequada |
| **1000 a 1500 ppm** | Moderado / Abafado | Sonolência; recomenda-se ventilação |
| **> 1500 ppm** | Crítico / Ar Viciado | Ventilação urgente recomendada |

---

## 5. Pré-aquecimento (Warm-Up)
O sensor necessita de aproximadamente **180 segundos (3 minutos)** após ser ligado para que a câmara óptica térmica e a lâmpada infravermelha atinjam o equilíbrio. Durante esse período:
- As leituras podem apresentar variações transitórias;
- A UI exibirá uma contagem regressiva de aquecimento.
