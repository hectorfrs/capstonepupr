import yaml
from lib.pressure_sensor import PressureSensor
from lib.valve_control import QwiicRelayController
from utils.iot_core import IoTCoreClient
from utils.greengrass import process_with_greengrass
import logging
import json
import os
import time

def load_config():
    """
    Carga la configuración específica de Raspberry Pi 2 desde un archivo YAML.
    """
    print("Cargando configuración para Raspberry Pi 2...")
    config_path = 'config/pi2_config.yaml'
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Archivo de configuración no encontrado en {config_path}")
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    print("Configuración cargada.")
    return config

def handle_valve_control(client, userdata, message):
    """
    Callback para manejar mensajes de control de válvulas recibidos a través de MQTT.

    :param client: Cliente MQTT.
    :param userdata: Información adicional del cliente MQTT.
    :param message: Mensaje recibido.
    """
    print(f"Mensaje de control de válvulas recibido: {message.payload}")
    try:
        data = json.loads(message.payload)
        action = data.get("action")
        if action == "activate_valve_1":
            relay_controller.activate_relay("valve_1")
        elif action == "activate_valve_2":
            relay_controller.activate_relay("valve_2")
        elif action == "deactivate_valve_1":
            relay_controller.deactivate_relay("valve_1")
        elif action == "deactivate_valve_2":
            relay_controller.deactivate_relay("valve_2")
        else:
            print(f"Acción desconocida: {action}")
    except Exception as e:
        print(f"Error al procesar mensaje de control de válvulas: {e}")

def handle_settings_update(client, userdata, message):
    """
    Callback para manejar mensajes de actualización de configuración recibidos a través de MQTT.

    :param client: Cliente MQTT.
    :param userdata: Información adicional del cliente MQTT.
    :param message: Mensaje recibido.
    """
    print(f"Mensaje de actualización de configuración recibido: {message.payload}")
    try:
        data = json.loads(message.payload)

        # Actualizar presión mínima y máxima
        min_pressure = data.get("min_pressure")
        max_pressure = data.get("max_pressure")
        if min_pressure is not None and max_pressure is not None:
            print(f"Actualizando rango de presión: min={min_pressure}, max={max_pressure}")
            pressure_sensor.min_pressure = min_pressure
            pressure_sensor.max_pressure = max_pressure

        # Actualizar direcciones de relés
        relay_addresses = data.get("relay_addresses")
        if relay_addresses:
            print(f"Actualizando direcciones de relés: {relay_addresses}")
            relay_controller.relay_addresses.update(relay_addresses)

        print("Configuración actualizada exitosamente.")
    except Exception as e:
        print(f"Error al procesar mensaje de actualización de configuración: {e}")

def read_and_publish_pressure(config, sensors, iot_client):
    """
    Lee los valores de los sensores de presión y publica los datos en AWS IoT Core.

    :param config: Configuración cargada desde el archivo YAML.
    :param sensors: Lista de sensores configurados.
    :param iot_client: Cliente MQTT para publicar los datos.
    """
    pressure_data = pressure_sensor.read_all_sensors(sensors)
    if pressure_data:
        # Procesar datos con Greengrass
        process_with_greengrass(config['greengrass']['group_name'], pressure_data)
        # Publicar datos en AWS IoT Core
        payload = {
            "device": "Raspberry Pi 2",
            "pressures": pressure_data
        }
        iot_client.publish(config['aws']['iot_topics']['sensor_data'], payload)
        print(f"Datos de presión publicados: {payload}")

def main():
    """
    Script principal para leer sensores, controlar válvulas y manejar señales externas.
    """
    global pressure_sensor
    global relay_controller

    # Cargar la configuración
    config = load_config()

    # Configurar logging
    logging.basicConfig(filename=config['logging']['log_file'], level=logging.INFO)
    print("Logging configurado.")

    # Inicializar sensores de presión
    pressure_sensor = PressureSensor(
        i2c_bus=1,
        min_pressure=config['pressure_sensors']['min_pressure'],
        max_pressure=config['pressure_sensors']['max_pressure']
    )

    # Inicializar controlador de válvulas
    relay_controller = QwiicRelayController(
        i2c_bus=1,
        relay_addresses=config['valves']['relay_module']['addresses']
    )

    # Inicializar cliente MQTT
    mqtt_client = IoTCoreClient(
        endpoint=config['aws']['iot_core_endpoint'],
        cert_path=config['aws']['cert_path'],
        key_path=config['aws']['key_path'],
        ca_path=config['aws']['ca_path']
    )
    mqtt_client.connect()

    # Suscribirse a tópicos MQTT
    mqtt_client.subscribe(config['aws']['iot_topics']['valve_control'], handle_valve_control)
    mqtt_client.subscribe(config['aws']['iot_topics']['settings_update'], handle_settings_update)

    mqtt_client.loop_start()

    # Leer y publicar datos de sensores periódicamente
    try:
        while True:
            read_and_publish_pressure(config, config['pressure_sensors']['sensors'], mqtt_client)
            time.sleep(10)  # Intervalo entre lecturas
    except KeyboardInterrupt:
        print("Apagando...")
    finally:
        mqtt_client.loop_stop()
        print("Programa finalizado.")

if __name__ == '__main__':
    main()
