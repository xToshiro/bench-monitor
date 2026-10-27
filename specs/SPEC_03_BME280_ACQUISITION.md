# SPEC 03: Aquisição de Dados do Sensor BME280

## 1. Visão Geral do Sensor
O **Bosch BME280** é um sensor digital de precisão que combina transdutores de:
- **Temperatura** (°C);
- **Umidade Relativa** (% RH);
- **Pressão Atmosférica** (hPa / bar).

Ele opera sob o protocolo de comunicação I2C, conectado aos pinos **SDA (GPIO 8)** e **SCL (GPIO 9)**.

---

## 2. Faixas de Operação e Precisão

| Grandeza | Faixa de Medição | Resolução | Precisão Típica |
| :--- | :--- | :--- | :--- |
| **Temperatura** | -40 °C a +85 °C | 0.01 °C | ±0.5 °C (a 25 °C) |
| **Umidade** | 0 % a 100 % RH | 0.008 % RH | ±3 % RH |
| **Pressão** | 300 hPa a 1100 hPa | 0.18 Pa | ±1.0 hPa (equivalente a ~±8 m) |

---

## 3. Configuração de Oversampling e Filtro IIR

Para operação estável em bancada sem ruído térmico gerado por correntes parasitas, o BME280 é inicializado no modo Normal com o seguinte perfil:

```cpp
bme.setSampling(Adafruit_BME280::MODE_NORMAL,     /* Modo operacional contínuo */
                Adafruit_BME280::SAMPLING_X2,     /* Oversampling de temperatura */
                Adafruit_BME280::SAMPLING_X16,    /* Oversampling de pressão */
                Adafruit_BME280::SAMPLING_X1,     /* Oversampling de umidade */
                Adafruit_BME280::FILTER_X16,      /* Coeficiente do filtro IIR */
                Adafruit_BME280::STANDBY_MS_500); /* Tempo de espera entre medições */
```

---

## 4. Grandezas Derivadas (Cálculos de Engenharia)

Além das variáveis brutas adquiridas dos registradores do sensor, o firmware calcula automaticamente:

### 4.1. Ponto de Orvalho (Dew Point - Fórmula de Magnus-Tetens)
$$T_{dew} = \frac{c \cdot \gamma(T, RH)}{b - \gamma(T, RH)}$$
onde:
$$\gamma(T, RH) = \frac{b \cdot T}{c + T} + \ln\left(\frac{RH}{100}\right)$$
Constantes: $b = 17.27$, $c = 237.7^\circ\text{C}$.

### 4.2. Altitude Barométrica Aproximada
Calculada pela equação hipsométrica internacional tendo como referência a pressão ao nível do mar padrão ($P_0 = 1013.25\text{ hPa}$):
$$\text{Altitude} = 44330 \cdot \left(1 - \left(\frac{P}{P_0}\right)^{\frac{1}{5.255}}\right)$$

---

## 5. Estrutura de Dados da Telemetria (`BME280Data`)

```cpp
struct BME280Data {
    bool valid;                 // true se a leitura foi bem-sucedida
    float temperature_c;        // Temperatura em graus Celsius (°C)
    float humidity_pct;         // Umidade relativa em percentual (%)
    float pressure_hpa;         // Pressão atmosférica em hectopascais (hPa)
    float altitude_m;           // Altitude estimada em metros (m)
    float dew_point_c;          // Ponto de orvalho calculado (°C)
    uint32_t sample_timestamp;  // Timestamp em milissegundos pós-boot
    uint32_t error_counter;     // Contador de falhas consecutivas de comunicação
};
```

---

## 6. Tratamento de Falhas e Watchdog do Sensor

1. **Auto-Detecção de Endereço:**
   O firmware testa sequencialmente o endereço primário `0x76` e o secundário `0x77`.
2. **Reconexão Quente (Hot-Plug Recovery):**
   Se uma leitura falhar por timeout ou NACK no barramento I2C:
   - O campo `valid` é marcado como `false`;
   - O contador de erros `error_counter` é incrementado;
   - Se ocorrerem mais de 3 falhas consecutivas, uma rotina de reset de barramento I2C (`i2c_bus_recover`) e reinicialização do periférico é disparada sem reiniciar o ESP32-C5.
