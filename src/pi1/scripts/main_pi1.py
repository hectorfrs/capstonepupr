import yaml
from lib.as7265x import AS7265x
from lib.mux_controller import MUXController
from utils.greengrass import process_with_greengrass
from utils import iot_core
import logging
import paho.mqtt.client as mqtt
import json
import os
from datetime import datetime

def load_config():
    """
    Carga la configuración específica de Raspberry Pi 1 desde un archivo YAML.
    """
    print("Loading configuration for Raspberry Pi 1...")
    config_path = 'config/pi1_config.yaml'
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    print("Configuration loaded.")
    return config

def save_data_to_csv(data, csv_path="/data/pi1_data.csv"):
    """
    Guarda los datos recolectados en un archivo CSV.

    :param data: Diccionario con los datos a guardar (timestamp y espectros).
    :param csv_path: Ruta del archivo CSV.
    """
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["timestamp", "sensor", "violet", "blue", "green", "yellow", "orange", "red"])
        if not file_exists:
            writer.writeheader()  # Escribir encabezado si el archivo no existe
        writer.writerow(data)
    print(f"Data saved to {csv_path}: {data}")

def on_settings_update(client, userdata, message):
    """
    Callback para manejar actualizaciones de configuración a través de MQTT.

    :param client: Cliente MQTT.
    :param userdata: Información adicional del cliente MQTT.
    :param message: Mensaje recibido con los nuevos ajustes.
    """
    print(f"Received settings update: {message.payload}")
    try:
        data = json.loads(message.payload)
        integration_time = data.get("integration_time")
        gain = data.get("gain")
        if integration_time or gain:
            print(f"Updating sensor settings: integration_time={integration_time}, gain={gain}")
            sensor.update_settings(integration_time=integration_time, gain=gain)
    except Exception as e:
        print(f"Failed to apply settings update: {e}")

def main():
    """
    Script principal para leer datos de los sensores AS7265x y publicar actualizaciones en AWS IoT Core.
    """
    # Cargar la configuración
    config = load_config()

    # Configurar logging
    logging.basicConfig(filename=config['logging']['log_file'], level=logging.INFO)
    print("Logging configured.")

    # Inicializar el MUX y los sensores
    mux = MUXController(i2c_bus=1, i2c_address=config['mux']['i2c_address'])
    sensors_config = config['mux']['channels']
    global sensor
    sensor = AS7265x(
        i2c_bus=config['sensors']['as7265x']['i2c_bus'],
        integration_time=config['sensors']['as7265x']['integration_time'],
        gain=config['sensors']['as7265x']['gain']
    )

    # Configurar MQTT
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_settings_update
    mqtt_client.connect(config['aws']['iot_core_endpoint'], 8883)
    mqtt_client.subscribe(config['aws']['iot_topics']['settings_update'])
    mqtt_client.loop_start()
    print("MQTT client configured and subscribed to settings update.")

    # Iterar a través de los sensores conectados al MUX
    for sensor_config in sensors_config:
        try:
            print(f"Switching to sensor: {sensor_config['sensor_name']} on channel {sensor_config['channel']}")
            mux.select_channel(sensor_config['channel'])  # Seleccionar el canal del sensor en el MUX

            # Configurar y leer datos del sensor
            sensor.configure_sensor()
            spectral_data = sensor.read_spectrum()
            print(f"Spectral data from {sensor_config['sensor_name']}: {spectral_data}")

            # Crear el payload
            payload = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sensor": sensor_config['sensor_name'],
                **spectral_data
            }

            # Procesar datos con Greengrass
            process_with_greengrass(config['greengrass']['group_name'], payload)

            # Publicar datos en AWS IoT Core
            iot_core.send_data_to_aws(
                config['aws']['iot_core_endpoint'],
                config['aws']['iot_topics']['sensor_data'],
                payload,
                config['aws']['cert_path'],
                config['aws']['key_path'],
                config['aws']['ca_path']
            )
            print(f"Data published for {sensor_config['sensor_name']}.")

            # Guardar los datos en CSV
            save_data_to_csv(payload)

        except Exception as e:
            print(f"Failed to process {sensor_config['sensor_name']}: {e}")
            logging.error(f"Failed to process {sensor_config['sensor_name']}: {e}")

            logging.error(f"Failed to apply settings update: {e}")
            print(f"Failed to apply settings update: {e}")

        finally:
            mux.disable_all_channels()  # Deshabilitar todos los canales después de cada operación

if __name__ == '__main__':
    main()
