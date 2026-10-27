# SPEC 04: Interface Gráfica do Display OLED SSD1306

## 1. Visão Geral do Display
O display gráfico OLED possui resolução de **128 x 64 pixels**, monocromático (azul/branco/amarelo-azul), controlado pelo circuito integrado **SSD1306** através do barramento I2C no endereço `0x3C` (padrão) com suporte a rotação contínua e páginas de métricas.

---

## 2. Layout da Tela e Zonas Visuais

A tela de 128x64 é particionada em duas zonas funcionais:

```
+-------------------------------------------------------------+ (y = 0)
| [BANCADA]    I2C:OK    PAG 1/3     [12s]                    | (Zona Superior: Header)
|-------------------------------------------------------------| (y = 11: Linha divisória)
|                                                             |
|                                                             |
|                       ÁREA DE DADOS                         | (Zona Inferior: Corpo de Métricas)
|                   (Tipografia ampliada)                     |
|                                                             |
|                                                             |
+-------------------------------------------------------------+ (y = 63)
```

---

## 3. Telas do Carrossel de Métricas (Pages)

O display cicla automaticamente a cada **4 segundos** (configurável em `config.h`) entre as seguintes visualizações:

### Tela 1: Clima e Conforto Térmico (Temperatura & Umidade)
- **Header:** `[CLIMA]` com indicador de página `1/3` e batimento cardíaco.
- **Linha 1:** Temperatura em fonte grande (ex: `27.4 °C`).
- **Linha 2:** Umidade relativa do ar em fonte média (ex: `Umid: 64.2%`).
- **Barra de progresso inferior:** Barra gráfica representando a umidade de 0 a 100%.

### Tela 2: Barometria e Altitude (Pressão & Elevação)
- **Header:** `[BAROMETRIA]` com indicador de página `2/3`.
- **Linha 1:** Pressão em hPa (ex: `1012.8 hPa`).
- **Linha 2:** Altitude calculada (ex: `Alt: 42 m`).
- **Linha 3:** Ponto de orvalho (ex: `Orvalho: 19.8 °C`).

### Tela 3: Diagnóstico de Hardware e Sistema
- **Header:** `[SISTEMA ESP32-C5]` com indicador de página `3/3`.
- **Linha 1:** CPU RISC-V 240 MHz - Uptime em minutos/segundos.
- **Linha 2:** Status do I2C: SDA=8, SCL=9 (Devices: OLED, BME280).
- **Linha 3:** Memória livre (Free Heap: `xxx KB`).

---

## 4. Animações e Micro-Interações
1. **Heartbeat Indicator:** No canto superior direito do header, um símbolo circular pulsa a cada segundo para indicar a vida da tarefa de renderização.
2. **Tela de Boot / Splash Screen:** Ao ligar o ESP32-C5, um logo estilizado da bancada com o texto `"ESP32-C5 BANCADA"` e barra de carregamento durante a detecção do barramento I2C.
3. **Alerta de Erro de Sensor:** Se o sensor BME280 for desconectado, o centro da tela exibe um aviso de atenção com `"SENSOR BME280 OFFLINE"` e instruções para checar a fiação nos pinos 8 e 9.
