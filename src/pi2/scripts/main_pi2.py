import sys
import os
import yaml
import time
import logging
import queue

from threading import Thread
from datetime import datetime
from utils.json_manager import generate_json, save_json
from utils.json_logger import configure_logging, log_detection
from utils.mqtt_publisher import MQTTPublisher
from lib.pressure_sensor import PressureSensorManager
from lib.valve_control import ValveControl
from lib.relay_control import RelayControl
from utils.networking import NetworkManager
from logging.handlers import RotatingFileHandler
from utils.greengrass import GreengrassManager


# Añadir el directorio principal de src/pi2 al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

class StreamToLogger:
    """
    Redirige una salida (stdout o stderr) al logger.
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message.strip():  # Evitar logs en blanco
            self.logger.log(self.level, message.strip())

    def flush(self):
        pass  # Necesario para compatibilidad con sys.stdout y sys.stderr

def configure_logging(config):
    """
    Configura los logs generales, de errores, de sensores y de MQTT.
    
    :param config: Diccionario con la configuración de logs desde config.yaml.
    """
    max_log_size = config.get("logging", {}).get("max_size_mb", 5) * 1024 * 1024
    backup_count = config.get("logging", {}).get("backup_count", 3)

    # Configuración del formato de los logs
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    # Crear directorio de logs si no existe
    for log_key in ['general_log_file', 'error_log_file', 'sensors_log_file', 'mqtt_log_file']:
        log_file = os.path.expanduser(config['logging'][log_key])
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    # Configurar manejadores para cada tipo de log
    loggers = {}

    # Logs generales
    general_handler = RotatingFileHandler(
        filename=config['logging']['general_log_file'],
        maxBytes=max_log_size,
        backupCount=backup_count,
    )
    general_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    general_logger = logging.getLogger("general")
    general_logger.setLevel(logging.INFO)
    general_logger.addHandler(general_handler)
    loggers['general'] = general_logger

    # Logs de errores
    error_handler = RotatingFileHandler(
        filename=config['logging']['error_log_file'],
        maxBytes=max_log_size,
        backupCount=backup_count,
    )
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    error_handler.setLevel(logging.ERROR)
    error_logger = logging.getLogger("error")
    error_logger.setLevel(logging.ERROR)
    error_logger.addHandler(error_handler)
    loggers['error'] = error_logger

    # Logs de sensores
    sensors_handler = RotatingFileHandler(
        filename=config['logging']['sensors_log_file'],
        maxBytes=max_log_size,
        backupCount=backup_count,
    )
    sensors_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    sensors_logger = logging.getLogger("sensors")
    sensors_logger.setLevel(logging.INFO)
    sensors_logger.addHandler(sensors_handler)
    loggers['sensors'] = sensors_logger

    # Logs de MQTT
    mqtt_handler = RotatingFileHandler(
        filename=config['logging']['mqtt_log_file'],
        maxBytes=max_log_size,
        backupCount=backup_count,
    )
    mqtt_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    mqtt_logger = logging.getLogger("mqtt")
    mqtt_logger.setLevel(logging.INFO)
    mqtt_logger.addHandler(mqtt_handler)
    loggers['mqtt'] = mqtt_logger

    # Redirigir stdout y stderr al logger después de configurarlo
    sys.stdout = StreamToLogger(logging.getLogger(), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger(), logging.ERROR)
    return loggers


def load_config(config_path="/home/raspberry-2/capstonepupr/src/pi2/config/pi2_config.yaml"):
    """
    Carga la configuración desde un archivo YAML.
    
    :param config_path: Ruta al archivo YAML.
    :return: Diccionario con la configuración cargada.
    """
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

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
    Función principal para la operación de Raspberry Pi #2.
    Incluye monitoreo de sensores de presión, control de válvulas y publicación en MQTT.
    """
    # Cargar configuración desde config.yaml
    print("Cargando config file.")
    config = load_config()

    # Configurar el sistema de logging
    print("Configurando logging.")
    loggers = configure_logging(config)
    general_logger = loggers['general']
    error_logger = loggers['error']
    sensors_logger = loggers['sensors']
    mqtt_logger = loggers['mqtt']

    logging.info("Sistema iniciado en Raspberry Pi #2.")
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
    try:
        # Leer configuración desde el archivo config.yaml
        sensors_config = config['pressure_sensors']['sensors']
        log_path = config['pressure_sensors'].get('log_path', "data/pressure_logs.json")
        pressure_manager = PressureSensorManager(sensors_config, log_path)
        
        if not pressure_manager.sensors:
            logging.error("No se detectaron sensores conectados. Terminando el programa.")
            return
        logging.info(f"Se inicializaron {len(pressure_manager.sensors)} sensores de presión correctamente.")
    except Exception as e:
        logging.error(f"Error inicializando sensores de presión: {e}")
        return

    # Inicializar cliente MQTT
    logging.info("Inicializando cliente MQTT...")
    try:
        mqtt_client = MQTTPublisher(config_path=config_path, local=True)
        mqtt_client.connect()
        logging.info("Conexión al broker MQTT exitosa.")
    except Exception as e:
        logging.error(f"Error al conectar con el broker MQTT: {e}")
        raise ConnectionError("Conexión MQTT no disponible.")
        return

    # Inicializar Greengrass Manager
    logging.info("Inicializando Greengrass...")
    try:
        greengrass_manager = GreengrassManager(config_path=config_path)
        logging.info("Greengrass Manager inicializado.")
    except Exception as e:
        logging.error(f"Error inicializando Greengrass Manager: {e}")
        return

    # Inicializar control de relés
    logging.info("Inicializando control de válvulas...")
    try:
        #mqtt_client = MQTTPublisher(config_path="/home/raspberry-2/capstonepupr/src/pi2/config/pi2_config.yaml", local=True)
        #mqtt_client.connect()
        relay_control = RelayControl(config['valves'], mqtt_client)
    except Exception as e:
        logging.error(f"Error inicializando control de válvulas: {e}")
        return

    # Inicializar buffer de datos
    data_queue = queue.Queue(maxsize=config['data_queue']['max_size'])
    logging.info(f"Queue de datos inicializada con tamaño máximo: {config['data_queue']['max_size']}")

    # Iniciar hilo para publicar datos
    def publish_data():
        while True:
            try:
                payload = data_queue.get()
                mqtt_client.publish(config['mqtt']['topics']['sensor_data'], payload)
                logging.info(f"Datos publicados en MQTT: {payload}")
                
                response = greengrass_manager.invoke_function(payload)
                logging.info(f"Datos procesados por Greengrass: {response}")

            except Exception as e:
                logging.error(f"Error publicando datos: {e}")
    
    publish_thread = Thread(target=publish_data,daemon=True)
    publish_thread.start()

    # Ciclo principal
    if not mqtt_client:
        logging.error("MQTT Client no está inicializado. Abortando control de válvulas.")
        return
    logging.info(f"Estado de mqtt_client antes de usar: {mqtt_client}")
    logging.info("Ejecutando ciclo principal...")
    try:
        while True:
            logging.info("Leyendo sensores de presión...")
            readings = sensors.read_all_sensors()
            for reading in readings:
                logging.info(f"Sensor: {reading['name']}, Pressure: {reading['pressure']} PSI")
                # Publicar datos a través de MQTT
                mqtt_client.publish("sensor/data", str(reading))

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

            # Enviar datos al buffer
            data_queue.put(generate_json(
                sensor_id=valve_name,
                pressure=pressure,
                valve_state="active" if pressure > config['pressure_sensors']['max_pressure'] else "inactive",
                action="read_pressure",
                metadata={}
                ))

            # Esperar antes de la siguiente lectura
            logging.info("Esperando %s segundos antes de la siguiente lectura.", config['sensors']['read_interval'])
            time.sleep(config['sensors']['read_interval'])

    except KeyboardInterrupt:
        logging.info("Interrupción por teclado. Terminando el programa.")
        logging.error(f"Error crítico en el programa: {e}", exc_info=True)
    finally:
        if mqtt_client:
            mqtt_client.disconnect()
            logging.info("Cliente MQTT desconectado.")
        logging.info("Programa terminado correctamente.")

if __name__ == '__main__':
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/raspberry-2/capstonepupr/src/pi2/logs/capstone_pi2.log"),
        logging.StreamHandler()
    ]
)
    main()
