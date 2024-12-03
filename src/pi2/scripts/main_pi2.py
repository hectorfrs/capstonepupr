import yaml
import time
import logging

from datetime import datetime
from utils.json_manager import generate_json, save_json
from utils.config_loader import load_config
from utils.json_loggerlogger import configure_logging, log_detection
from utils.mqtt_client import MQTTClient
from utils.pressure_sensor import PressureSensor
from utils.relay_control import RelayControl
from utils.networking import NetworkManager

import sys
import os
# Añadir el directorio principal de src/pi2 al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

def configure_logging(config):
    log_file = os.path.expanduser(config['logging']['log_file'])  # Expande '~' al directorio del usuario
    log_dir = os.path.dirname(log_file)

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    print(f"Logging configurado en {log_file}.")

def load_config(config_path="/home/raspberry-2/capstonepupr/src/pi2/config/pi2_config.yaml"):
    """
    Carga la configuración desde un archivo YAML.
    
    :param config_path: Ruta al archivo YAML.
    :return: Diccionario con la configuración cargada.
    """
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def main():
    """
    Función principal para la operación de Raspberry Pi #2.
    Incluye monitoreo de sensores de presión, control de válvulas y publicación en MQTT.
    """
    # Cargar configuración desde config.yaml
    config = load_config()

    # Configurar el sistema de logging
    logging.info("Configurando logging.")
    configure_logging(config)

    logging.info("Sistema iniciado en Raspberry Pi #1.")
    #print("Logging configurado.")

    # Configurar red
    logging.info("Verificando conexión a Internet...")
    try:
        network_manager = NetworkManager(config_path="/home/raspberry-2/capstonepupr/src/pi2/config/pi2_config.yaml")
        if not network_manager.check_connection():
            logging.error("No hay conexión a Internet. Verifique la configuración de red.")
            raise ConnectionError("Conexión de red no disponible.")
    except Exception as e:
        logging.error(f"Error configurando la red: {e}")
        raise
    logging.info("Conexión a Internet verificada.")

    # Inicializar sensores de presión
    logging.info("Inicializando sensores de presión...")
    sensors = [PressureSensor(sensor_cfg) for sensor_cfg in config['pressure_sensors']['sensors']]

    # Inicializar control de relés para las válvulas
    logging.info("Inicializando control de válvulas...")
    relay_control = RelayControl(config['valves'])

    # Configurar cliente MQTT
    # logging.info("Configurando cliente MQTT...")
    # mqtt_client = MQTTClient(config['mqtt'])
    # mqtt_client.connect()

        # Inicializar cliente MQTT
    logging.info("Inicializando cliente MQTT...")
    mqtt_client = MQTTPublisher(config_path="/home/raspberry-2/capstonepupr/src/pi2/config/pi2_config.yaml", local=True)
    try:
        mqtt_client.connect()
        logging.info("Conexión al broker MQTT exitosa.")
    except Exception as e:
        logging.error(f"Error al conectar con el broker MQTT: {e}")
        raise ConnectionError("Conexión MQTT no disponible.")

     # Inicializar Greengrass Manager
    greengrass_manager = GreengrassManager(config_path="/home/raspberry-2/capstonepupr/src/pi2/config/pi2_config.yaml")

    # Inicializar buffer de datos
    data_queue = Queue()

    # Iniciar hilo para publicar datos
    publish_thread = Thread(
        target=publish_data,
        args=(mqtt_client, greengrass_manager, config['mqtt']['topics']['sensor_data'], data_queue),
        daemon=True
    )
    publish_thread.start()

    try:
        while True:
            logging.info("Leyendo sensores de presión...")
            readings = []
            for sensor in sensors:
                pressure = sensor.read_pressure()
                readings.append({
                    'sensor_name': sensor.name,
                    'pressure': pressure,
                    'status': "OK" if config['pressure_sensors']['min_pressure'] <= pressure <= config['pressure_sensors']['max_pressure'] else "ALERT"
                })

                # Controlar válvulas según la presión
                if pressure > config['pressure_thresholds']['high']:
                    logging.info("Presión alta detectada en %s. Activando válvula.", sensor.name)
                    relay_control.activate(sensor.name)
                elif pressure < config['pressure_thresholds']['low']:
                    logging.info("Presión baja detectada en %s. Desactivando válvula.", sensor.name)
                    relay_control.deactivate(sensor.name)

            # Registrar lecturas
            log_data = {
                'device_id': config['network']['ethernet']['ip'],
                'timestamp': time.strftime("%Y-%m-%dT%H:%M:%S"),
                'readings': readings
            }
            logging.info("Registrando datos de sensores: %s", log_data)
            log_detection(log_data, config['logging']['log_file'])

            # Publicar datos en MQTT
            logging.info("Publicando datos en MQTT...")
            mqtt_client.publish(
                topic=config['mqtt']['topics']['sensor_data'],
                payload=log_data
            )

            # Esperar antes de la siguiente lectura
            logging.info("Esperando %s segundos antes de la siguiente lectura.", config['sensors']['read_interval'])
            time.sleep(config['sensors']['read_interval'])

    except KeyboardInterrupt:
        logging.info("Interrupción por teclado. Terminando el programa.")
    finally:
        mqtt_client.disconnect()
        logging.info("Cliente MQTT desconectado.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
