import yaml
import logging
import os
import time
from datetime import datetime
from utils.mqtt_publisher import MQTTPublisher
from utils.greengrass import process_with_greengrass
from utils.sensors import PressureSensor
from utils.valve_control import ValveController


def load_config():
    """
    Carga la configuración desde el archivo YAML.
    """
    print("Cargando configuración para Raspberry Pi 2...")
    config_path = 'config/pi2_config.yaml'
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"No se encontró el archivo de configuración en {config_path}")
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    print("Configuración cargada.")
    return config


def main():
    """
    Función principal para manejar sensores de presión, válvulas y publicación de datos.
    """
    # Cargar configuración
    config = load_config()

    # Configurar logging
    logging.basicConfig(filename=config['logging']['log_file'], level=logging.INFO)
    print("Logging configurado.")

    # Inicializar sensores de presión
    sensors = [
        PressureSensor(
            i2c_address=sensor['i2c_address'],
            min_pressure=config['pressure_sensors']['min_pressure'],
            max_pressure=config['pressure_sensors']['max_pressure']
        )
        for sensor in config['pressure_sensors']['sensors']
    ]

    # Inicializar controlador de válvulas
    valve_controller = ValveController(
        relay_addresses=config['valves']['relay_module']['addresses'],
        trigger_level=config['valves']['trigger_level']
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

    # Bucle principal para manejar sensores y válvulas
    while True:
        try:
            for sensor in sensors:
                # Leer datos de presión
                pressure = sensor.read_pressure()
                payload = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "sensor": sensor.i2c_address,
                    "pressure": pressure
                }

                # Publicar datos de presión en MQTT local y AWS IoT Core
                local_publisher.publish(config['mqtt']['topics']['pressure_data'], payload)
                aws_publisher.publish(config['aws']['iot_topics']['pressure_data'], payload)

                # Procesar datos localmente con Greengrass
                response = process_with_greengrass(config['greengrass']['functions'][0]['arn'], payload)
                print(f"Respuesta de Greengrass: {response}")

                # Control de válvulas basado en presión
                if sensor.i2c_address == config['pressure_sensors']['sensors'][0]['i2c_address']:  # Entrada válvula 1
                    if pressure > config['pressure_sensors']['max_pressure']:
                        valve_controller.deactivate_valve('valve_1')
                    else:
                        valve_controller.activate_valve('valve_1')

                elif sensor.i2c_address == config['pressure_sensors']['sensors'][2]['i2c_address']:  # Entrada válvula 2
                    if pressure > config['pressure_sensors']['max_pressure']:
                        valve_controller.deactivate_valve('valve_2')
                    else:
                        valve_controller.activate_valve('valve_2')

            # Intervalo entre lecturas
            time.sleep(1)

        except Exception as e:
            logging.error(f"Error en el bucle principal: {e}")
            print(f"Error en el bucle principal: {e}")


if __name__ == '__main__':
    main()
