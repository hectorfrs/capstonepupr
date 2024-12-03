import yaml
import time
import logging
from threading import Thread
from queue import Queue
from datetime import datetime
from asyncio import Handle

from lib.mux_controller import MUXController
from lib.as7265x import CustomAS7265x
from utils.mqtt_publisher import MQTTPublisher
from utils.greengrass import GreengrassManager
from utils.networking import NetworkManager
from utils.json_manager import generate_json, save_json
from utils.json_logger import log_detection

import sys
import os
# Agregar la ruta del proyecto al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# Agregar el directorio 'lib' al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

def load_thresholds(config, material):
    """
    Carga los umbrales espectrales para un material específico.
    """
    return config["plastic_thresholds"].get(material, [])

def detect_material(config):
    """
    Simula la detección de materiales plásticos utilizando datos de configuración.
    """
    # Datos espectrales simulados para la demostración
    simulated_spectral_data = {
        "channel_1": 150,
        "channel_2": 180,
        "channel_3": 100
    }

    # Comparar datos simulados con umbrales configurados
    detected_material = "Otros"  # Valor predeterminado
    confidence = 0.0

    for material, thresholds in config["plastic_thresholds"].items():
        matches = all(
            thresholds[i][0] <= simulated_spectral_data[f"channel_{i+1}"] <= thresholds[i][1]
            for i in range(len(thresholds))
        )
        if matches:
            detected_material = material
            confidence = 1.0  # Simula confianza máxima (puede calcularse dinámicamente)
            break

    detection_data = {
        "material": detected_material,
        "confidence": confidence,
        "spectral_data": simulated_spectral_data,
        "sensor_id": config["mux"]["channels"][0]["sensor_name"],  # Primer sensor del MUX
        "mux_channel": config["mux"]["channels"][0]["channel"],  # Canal del MUX
        "timestamp": datetime.now().isoformat(),
        "processing_time_ms": 120,  # Simulado
        "device_id": config["network"]["ethernet"]["ip"],  # Dirección IP del dispositivo
        "location": "line_1_zone_A"  # Estático, puedes actualizar si es dinámico
    }

    return detection_data

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

def load_config(config_path="/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml"):
    """
    Carga la configuración desde un archivo YAML.
    
    :param config_path: Ruta al archivo YAML.
    :return: Diccionario con la configuración cargada.
    """
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def identify_plastic(spectral_data, thresholds):
    """
    Identifica el tipo de plástico según el espectro y los umbrales configurados.

    :param spectral_data: Datos espectroscópicos calibrados.
    :param thresholds: Umbrales para cada tipo de plástico.
    :return: Tipo de plástico detectado (str) o None si no coincide.
    """
    for plastic_type, ranges in thresholds.items():
        match = all(ranges[i][0] <= spectral_data[i] <= ranges[i][1] for i in range(len(ranges)))
        if match:
            return plastic_type
    return None


def process_sensor(mux, sensor, channel, sensor_name, thresholds, data_queue):
    """
    Lee datos de un sensor específico y los encola para procesamiento.

    :param mux: Instancia del controlador MUX.
    :param sensor: Instancia del sensor AS7265x.
    :param channel: Canal del MUX.
    :param sensor_name: Nombre del sensor.
    :param thresholds: Umbrales para identificación de plásticos.
    :param data_queue: Buffer para almacenar datos procesados.
    """
    try:
        mux.select_channel(channel)
        logging.info(f"Canal {channel} activado para el sensor {sensor_name}.")
        
        spectral_data = sensor.read_spectrum()
        logging.info(f"Datos leídos del sensor {sensor_name}: {spectral_data}")

        detected_material = identify_material(spectral_data, thresholds)
        logging.info(f"Material detectado por {sensor_name}: {detected_material}")

        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sensor": sensor_name,
            "material": detected_material,
            **spectral_data
        }

        data_queue.put(payload)
        logging.info(f"Datos encolados para publicación: {payload}")

    except Exception as e:
        logging.error(f"Error procesando datos del sensor {sensor_name} en el canal {channel}: {e}")


def publish_data(mqtt_client, greengrass_manager, topic, data_queue):
    """
    Publica datos del buffer a MQTT y AWS IoT Core.

    :param mqtt_client: Instancia del cliente MQTT.
    :param greengrass_manager: Instancia del gestor de Greengrass.
    :param topic: Tópico MQTT para publicar.
    :param data_queue: Buffer para obtener datos procesados.
    """
    while True:
        try:
            payload = data_queue.get()
            mqtt_client.publish(topic, payload)
            logging.info(f"Datos publicados en MQTT: {payload}")
            
            response = greengrass_manager.invoke_function(payload)
            logging.info(f"Datos procesados por Greengrass: {response}")

        except Exception as e:
            logging.error(f"Error publicando datos: {e}")


def main():
    """
    Función principal para manejar la lógica del Raspberry Pi 1.
    """
    # Cargar configuración
    config = load_config()

    
    # Configurar logging
    configure_logging(config)
    # logging.basicConfig(
    #     filename=config['logging']['log_file'],
    #     level=logging.INFO,
    #     format='%(asctime)s %(levelname)s: %(message)s'
    # )
    logging.info("Sistema iniciado en Raspberry Pi #1.")
    #print("Logging configurado.")

    # Configurar red
    logging.info("Verificando conexión a Internet...")
    try:
        network_manager = NetworkManager(config_path="/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml")
        if not network_manager.check_connection():
            logging.error("No hay conexión a Internet. Verifique la configuración de red.")
            raise ConnectionError("Conexión de red no disponible.")
    except Exception as e:
        logging.error(f"Error configurando la red: {e}")
        raise
    logging.info("Conexión a Internet verificada.")

    # Inicializar MUX
    logging.info("Inicializando MUX...")
    mux = MUXController(
        i2c_bus=config['sensors']['as7265x']['i2c_bus'],
        i2c_address=config['mux']['i2c_address']
    )
    logging.info(f"MUX conectado en la dirección 0x{config['mux']['i2c_address']:02X}.")
    
    # Inicializar sensores
    logging.info("Inicializando sensores AS7265x...")
    sensors_config = config['mux']['channels']
    thresholds = config['plastic_thresholds']

    sensors = [
        CustomAS7265x(config_path="/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml") for _ in sensors_config
    ]
    logging.info(f"{len(sensors)} sensores configurados con éxito.")

    # Inicializar cliente MQTT
    logging.info("Inicializando cliente MQTT...")
    mqtt_client = MQTTPublisher(config_path="/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml", local=True)
    try:
        mqtt_client.connect()
        logging.info("Conexión al broker MQTT exitosa.")
    except Exception as e:
        logging.error(f"Error al conectar con el broker MQTT: {e}")
        raise ConnectionError("Conexión MQTT no disponible.")


    # Inicializar Greengrass Manager
    greengrass_manager = GreengrassManager(config_path="/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml")

    # Inicializar buffer de datos
    data_queue = Queue()

    # Iniciar hilo para publicar datos
    publish_thread = Thread(
        target=publish_data,
        args=(mqtt_client, greengrass_manager, config['mqtt']['topics']['sensor_data'], data_queue),
        daemon=True
    )
    publish_thread.start()

    while True:
        try:
            for sensor_idx, sensor_config in enumerate(sensors_config):
                logging.info(f"Procesando datos del sensor {sensor_config['sensor_name']} en el canal {sensor_config['channel']}...")
                process_sensor(
                    mux=mux,
                    sensor=sensors[sensor_idx],
                    channel=sensor_config['channel'],
                    sensor_name=sensor_config['sensor_name'],
                    thresholds=thresholds,
                    data_queue=data_queue
                )
            time.sleep(config['sensors']['read_interval'])

        except Exception as e:
            logging.error(f"Error en el loop principal: {e}")

    logging.info("Iniciando detección de materiales...")

    # Detectar material
    detection_result = detect_material(config)
    logging.info(f"Material detectado: {detection_result}")

    # Registrar detección
    log_detection(detection_result, config_path="/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml")

if __name__ == "__main__":
    main()
