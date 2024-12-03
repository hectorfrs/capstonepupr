# Raspberry Pi #3: Broker MQTT y Controlador

Este dispositivo actúa como el broker MQTT y controlador central para coordinar la comunicación entre los demás dispositivos.

## Estructura de Directorios

```
src/pi3/
- config/
  - pi3_config.yaml          # Configuración del dispositivo
- data/                      # Datos generados
- lib/                       # Bibliotecas utilizadas
- utils/                     # Utilidades adicionales
- update_config_pi3.py       # Publica actualizaciones de configuración
- data_collector_pi3.py      # Recolecta datos de otros dispositivos
- publish_data_pi3.py        # Publica datos combinados
- README.md                  # Este archivo
```

## Scripts

### 1. `update_config_pi3.py`
- Envía actualizaciones de configuración a los dispositivos en los tópicos `pi1/settings_update` y `pi2/settings_update`.

### 2. `data_collector_pi3.py`
- Recolecta datos desde los tópicos `pi1/sensor_data` y `pi2/sensor_data`.

### 3. `publish_data_pi3.py`
- Publica datos combinados en el tópico `pi3/data`.

## Dependencias
- Python 3
- Bibliotecas:
  - `paho-mqtt`
  - `pyyaml`

## Uso

1. **Enviar actualizaciones de configuración:**
   ```bash
   python3 update_config_pi3.py
   ```

2. **Recolectar datos de sensores:**
   ```bash
   python3 data_collector_pi3.py
   ```

3. **Publicar datos combinados:**
   ```bash
   python3 publish_data_pi3.py
   ```
