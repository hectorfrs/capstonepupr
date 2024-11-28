import yaml
import logging
import os
import time
from datetime import datetime
from lib.mux_controller import MUXController
from lib.as7265x import AS7265x
from utils.mqtt_publisher import MQTTPublisher
from utils.greengrass import process_with_greengrass
from utils.networking import NetworkManager


def load_config():
    """
    Carga la configuración desde el archivo YAML.
    """
    print("Cargando configuración para Raspberry Pi 1...")
    config_path = 'config/pi1_config.yaml'
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"No se encontró el archivo de configuración en {config_path}")
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    print("Configuración cargada.")
    return config


def main():
    """
    Función principal para manejar el flujo de datos del sensor AS7265x.
    """
    # Cargar configuración
    config = load_config()

    # Configurar logging
    logging.basicConfig(filename=config['logging']['log_file'], level=logging.INFO)
    print("Logging configurado.")

    # Inicializar MUX y sensores
    mux = MUXController(i2c_bus=1, i2c_address=config['mux']['i2c_address'])
    sensors_config = config['mux']['channels']
    sensor = AS7265x(
        i2c_bus=config['sensors']['as7265x']['i2c_bus'],
        integration_time=config['sensors']['as7265x']['integration_time'],
        gain=config['sensors']['as7265x']['gain']
    )

    # Configurar clientes MQTT
    local_publisher = MQTTPublisher(endpoints=config['mqtt']['broker_addresses'], local=True)
    local_publisher.connect(port=config['mqtt']['port'])

    aws_publisher = MQTTPublisher(
        endpoints=config['aws']['iot_core_endpoint'],
        cert_path=config['aws']['cert_path'],
        key_path=config['aws']['key_path'],
        ca_path=config['aws']['ca_path']
    )
    aws_publisher.connect()

    # Loop principal para lectura de sensores y publicación de datos
    while True:
        try:
            for sensor_config in sensors_config:
                print(f"Conmutando al sensor: {sensor_config['sensor_name']} en el canal {sensor_config['channel']}...")
                mux.select_channel(sensor_config['channel'])  # Seleccionar el canal del sensor en el MUX

                # Leer datos del sensor
                spectral_data = sensor.read_spectrum()
                payload = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "sensor": sensor_config['sensor_name'],
                    **spectral_data
                }

                # Publicar datos en MQTT local y AWS IoT Core
                local_publisher.publish(config['mqtt']['topics']['sensor_data'], payload)
                aws_publisher.publish(config['aws']['iot_topics']['sensor_data'], payload)

                # Procesar datos localmente con Greengrass
                response = process_with_greengrass(config['greengrass']['functions'][0]['arn'], payload)
                print(f"Respuesta de Greengrass: {response}")

            # Deshabilitar todos los canales del MUX después de cada ciclo
            mux.disable_all_channels()

            # Intervalo entre lecturas
            time.sleep(1)

        except Exception as e:
            logging.error(f"Error en el loop principal: {e}")
            print(f"Error en el loop principal: {e}")


if __name__ == '__main__':
    main()
