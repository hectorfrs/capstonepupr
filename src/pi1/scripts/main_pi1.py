#main_pi1.py - Script principal para el Raspberry Pi 1.

# Encabezado
import sys
import os
import subprocess
import yaml
import time
import logging
import json
from threading import Thread
from queue import Queue
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Importar módulos personalizados
from lib.mux_manager import MUXManager
from utils.sensor_manager import SensorManager
from lib.as7265x import CustomAS7265x
from utils.mqtt_publisher import MQTTPublisher
from utils.greengrass import GreengrassManager
from utils.network_manager import NetworkManager
from utils.json_logger import log_detection
from utils.alert_manager import AlertManager
from utils.performance_tracker import PerformanceTracker
from utils.real_time_config import RealTimeConfigManager
from lib.sensor_diagnostics import run_sensor_diagnostics
from lib.mux_diagnostics import run_mux_diagnostics

# Agregar la ruta del proyecto al PYTHONPATH
#print(sys.path)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append("/usr/local/lib/python3.11/dist-packages")

# Configuración de constantes
MAX_RETRIES = 3
DIAGNOSTICS_INTERVAL = 300  # Intervalo de diagnóstico en segundos
config_path = "/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml"

# Clase Auxiliar para redirigir la salida
class StreamToLogger:
    """
    Redirige stdout y stderr al logger.
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message.strip():
            self.logger.log(self.level, message.strip())

    def flush(self):
        pass

# Configuración de los logs
def configure_logging(config):
    """
    Configura el sistema de logging.
    """
    log_file = os.path.expanduser(config['logging']['log_file'])    
    log_dir = os.path.dirname(log_file)
    error_log_file = config["logging"]["error_log_file"]
    max_log_size = config.get("logging", {}).get("max_size_mb", 5) * 1024 * 1024                # Tamaño máximo en bytes
    backup_count = config.get("logging", {}).get("backup_count", 3)                             # Número de archivos de respaldo

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if len(logging.getLogger().handlers):
        return  # Evitar múltiples configuraciones
    
    # Configuración del formato de los logs con fecha y hora
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        filename=log_file,                                                                                          # Archivo de logs
        level=logging.DEBUG if config.get("system", {}).get("enable_detailed_logging", False) else logging.INFO,    # Nivel de logs
        format=LOG_FORMAT,                                                                                          # Formato del log                                         
        datefmt=DATE_FORMAT,                                                                                        # Formato de la fecha                                     
)
    
    # Configuración del RotatingFileHandler
    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=max_log_size,  # Tamaño máximo del archivo en bytes
        backupCount=backup_count,  # Número de archivos de respaldo
    )
    handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT))
    logging.getLogger().addHandler(handler)

    # Configuración del manejador para logs de errores
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT))

    # Agregar manejadores al logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if config.get("enable_detailed_logging", False) else logging.INFO)
    logger.addHandler(handler)
    logger.addHandler(error_handler)

    # Redirigir stdout y stderr al logger
    sys.stdout = StreamToLogger(logging.getLogger(), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger(), logging.ERROR)

    print(f"Logging configurado en {log_file}.")

def validate_config(config):
    """
    Valida la configuración para asegurar que todas las claves necesarias estén presentes.
    """
    required_keys = {
        'mux': ['i2c_address', 'i2c_bus', 'channels'],
        'sensors': ['as7265x', 'read_interval']
    }
    for section, keys in required_keys.items():
        if section not in config:
            raise KeyError(f"Sección faltante en configuración: {section}")
        for key in keys:
            if key not in config[section]:
                raise KeyError(f"Clave faltante en configuración [{section}]: {key}")
    logging.info("Validación de configuración completada.")


#Clasificacion y Deteccion de Plasticos
def classify_material(spectral_data, thresholds):
    """
    Clasifica el material según los umbrales definidos en el archivo config.yaml.

    :param spectral_data: Datos espectrales del sensor.
    :param thresholds: Umbrales definidos en config.yaml.
    :return: Tipo de material detectado.
    """
    try:
        for material, ranges in thresholds.items():
            if all(ranges[i][0] <= spectral_data[i] <= ranges[i][1] for i in range(len(ranges))):
                return material
        return "Otros"
    except Exception as e:
        logging.error(f"Error detectando material: {e}")
        return "Error"

# Activar Válvula
def activate_valve(material, mqtt_client):
    """
    Envía un comando al Raspberry Pi 2 para activar la válvula correspondiente.

    :param material: Tipo de material detectado.
    :param mqtt_client: Cliente MQTT para publicar comandos.
    """
    valve_mapping = {
        "PET": 1,
        "HDPE": 2
    }

    if material in valve_mapping:
        payload = {
            "material": material,
            "valve": valve_mapping[material],
            "timestamp": datetime.now().isoformat()
        }
        mqtt_client.publish(VALVE_CONTROL_TOPIC, json.dumps(payload))
        logging.info(f"Comando enviado para activar válvula {valve_mapping[material]} para material {material}.")

# Publicación de Datos
def publish_data(mqtt_client, greengrass_manager, topic, data_queue, alert_manager):
    """
    Publica datos encolados a MQTT y AWS IoT Core.
    """
    while True:
        try:
            data = data_queue.get(timeout=5)

            # Publicar datos en MQTT Localmente
            mqtt_client.publish(topic, data)
            logging.info(f"Datos publicados en MQTT: {data}")
            
            # Publicar datos en AWS IoT Core
            response = greengrass_manager.invoke_function(data)
            logging.info(f"Datos publicados en MQTT y procesados por Greengrass: {data} | Respuesta: {response}")
            
        except Exception as e:
            logging.error(f"Error publicando datos: {e}")
            alert_manager.send_alert(
                level="CRITICAL",
                message="Error al publicar datos",
                metadata={"error": str(e)}
            )

# Ahorro de energia
def run_power_saving_mode(sensors, mux_manager, enabled):
    """
    Activa el modo de ahorro de energía si está habilitado.
    """
    if not enabled:
        logging.info("Modo de ahorro de energía deshabilitado.")
        return

    logging.info("Habilitando modo de ahorro de energía...")
    try:
        for sensor in sensors:
            if hasattr(sensor, "power_off"):
                sensor.power_off()
                logging.info(f"Sensor {sensor.name} apagado para ahorro de energía.")
            else:
                logging.warning(f"El sensor {sensor.name} no tiene un método 'power_off'.")
        mux_manager.disable_all_channels()
        logging.info("Todos los canales del MUX han sido desactivados.")
    except Exception as e:
        logging.error(f"Error en el modo de ahorro de energía: {e}")


# Diagnostico de Componentes
def run_diagnostics(config, mux_manager, sensors, alert_manager):
    """
    Ejecuta diagnósticos de sensores y MUX si están habilitados.
    """
    if config['system']['enable_sensor_diagnostics']:
        logging.info("Ejecutando diagnósticos de sensores...")
        for sensor in sensors:
            try:
                temp = sensor.read_temperature()
                logging.info(f"Temperatura del sensor {sensor.name}: {temp:.2f} °C")
            except Exception as e:
                logging.error(f"Error diagnosticando sensor {sensor.name}: {e}")
                alert_manager.send_alert(
                    level="WARNING",
                    message=f"Error diagnosticando sensor {sensor.name}",
                    metadata={"error": str(e)}
                )

    if config['system']['enable_mux_diagnostics']:
        logging.info("Ejecutando diagnósticos del MUX...")
        run_mux_diagnostics(mux_manager, [ch['channel'] for ch in config['mux']['channels']], alert_manager)

# Reinicio Automatico
def restart_system(config):
    """
    Reinicia el sistema en caso de falla crítica si está habilitado en el config.yaml.
    """
    MAX_RETRIES = 3
    retries = 0
    while retries < MAX_RETRIES:
        try:
            if config['system'].get('enable_auto_restart', False):
                logging.critical("Reiniciando sistema por error crítico según configuración...")
                time.sleep(60)
            try:
                subprocess.run(["sudo", "reboot"], check=True)
            except Exception as e:
                logging.error(f"Error al intentar reiniciar el sistema: {e}")
            else:
                logging.error("Reinicio automático deshabilitado en configuración.")
                break
        except Exception as e:
            retries += 1
            logging.critical(f"Reinicio {retries}/{MAX_RETRIES} debido a error crítico: {e}")
        if retries >= MAX_RETRIES:
            logging.critical("Se alcanzó el máximo de reinicios. Abortando.")
            sys.exit(1)

def initialize_mux(config, alert_manager):
    try:
        mux_manager = MUXManager(
            i2c_bus=config['mux']['i2c_bus'],
            i2c_address=config['mux']['i2c_address'],
            alert_manager=alert_manager,
            config=config
        )
        if not mux_manager.is_mux_connected():
            raise RuntimeError("MUX no conectado o no accesible.")
        logging.info("MUX inicializado correctamente.")
        return mux_manager
    except Exception as e:
        logging.critical(f"Error inicializando el MUX: {e}")
        alert_manager.send_alert(
            level="CRITICAL",
            message="Error inicializando el MUX.",
            metadata={"error": str(e)}
        )
        raise



# Inicialización de Sensores
def initialize_sensors(config, mux_manager):
    try:
        sensor_manager = SensorManager(config=config, mux_manager=mux_manager)
        sensor_manager.initialize_sensors(mux_manager)
        return sensor_manager.sensors
    except Exception as e:
        logging.critical(f"Error inicializando sensores: {e}")
        raise


def process_channels(mux_manager):
    try:
        active_channels = mux_manager.detect_active_channels()
        for channel in active_channels:
            try:
                mux_manager.activate_channel(channel)
                logging.info(f"Canal {channel} activado.")
                # Otras operaciones aquí
            finally:
                mux_manager.deactivate_channel(channel)
    except Exception as e:
        logging.error(f"Error procesando canales del MUX: {e}")

def process_sensor(sensor, channel, mux_manager, alert_manager):
    """
    Procesa un sensor específico, validando su estado antes de realizar operaciones.
    """
    try:
        if not sensor.is_connected():
            raise RuntimeError(f"Sensor {sensor.name} no conectado.")
        
        if sensor.is_powered_off():
            raise RuntimeError(f"Sensor {sensor.name} está apagado. No se puede leer datos.")

        mux_manager.activate_channel(channel)
        data = sensor.read_advanced_spectrum()
        logging.info(f"Datos del sensor {sensor.name}: {data}")

    except Exception as e:
        logging.error(f"Error procesando el sensor {sensor.name}: {e}")
        alert_manager.send_alert(
            level="WARNING",
            message=f"Error procesando sensor {sensor.name}",
            metadata={"channel": channel, "error": str(e)},
        )
    finally:
        mux_manager.deactivate_all_channels()

# Funcion Principal
def main():
    """
    Función principal del sistema.
    """
    print("Iniciando Sistema...")
    retries = 0
    config_manager = None   # Inicialización temprana
    mqtt_client = None      # Inicialización temprana
    network_manager = None  # Inicialización temprana
    alert_manager = None    # Inicialización temprana
    mux_manager = None      # Inicialización temprana
    sensors = []            # Inicialización temprana
    while retries < MAX_RETRIES:
        try:
            # Cargar configuración
            config_manager = RealTimeConfigManager(config_path)
            config_manager.start_monitoring()
            config = config_manager.get_config()
            validate_config(config)

            # Configurar logging
            configure_logging(config)
            logging.info("Sistema iniciado en Raspberry Pi #1...")

            # Inicializar Alert Manager
            alert_manager = AlertManager(
                mqtt_client=None,
                alert_topic=config['mqtt']['topics']['alerts'],
                local_log_path=config['logging']['log_file']
            )

            # Configurar red y monitoreo
            logging.info("Iniciando monitoreo de red...")
            network_manager = NetworkManager(config)
            network_manager.start_monitoring()
            logging.info("Monitoreo de red iniciado.")

            # Enviar alerta de red
            if not network_manager.is_connected():
                alert_manager.send_alert(
                    level="CRITICAL",
                    message="No hay conexión a Internet.",
                    metadata={"ethernet_ip": config['network']['ethernet']['ip']}
                )

            # Inicializar MQTT Client
            mqtt_client = MQTTPublisher(config_path)
            mqtt_client.connect()

            # Inicialización del MUX
            logging.info("Inicializando MUX...")
            mux_manager = initialize_mux(config, alert_manager)

            if mux_manager is None:
                logging.critical("MUXManager no se inicializó correctamente. Abortando.")
                raise RuntimeError("MUXManager no inicializado")
            logging.info("MUX inicializado correctamente.")
            # Detectar y Actualizar Canales Activos
            try:
                active_channels = mux_manager.detect_active_channels()
                config_manager.set_value('mux', 'active_channels', active_channels)
                logging.info(f"Canales activos detectados y actualizados: {active_channels}")
            except Exception as e:
                logging.critical(f"Error detectando canales activos: {e}")
                alert_manager.send_alert(
                    level="CRITICAL",
                    message="Error detectando canales activos",
                    metadata={"error": str(e)},
                )
                raise RuntimeError("Error detectando canales activos")

            # Inicializar Greengrass Manager
            logging.info("Inicializando Greengrass Manager...")
            greengrass_manager = GreengrassManager(config_path=config_manager.config_path)

            # Inicializar sensores
            logging.info("Inicializando sensores...")
            sensors = initialize_sensors(config, mux_manager)

            # Diagnósticos iniciales
            run_diagnostics(config, mux_manager, sensors, alert_manager)
            
            # Modo de ahorro de energía
            run_power_saving_mode(mux_manager, sensors, config['system']['enable_power_saving'])

            # Configurar hilo de publicación de datos
            data_queue = Queue(maxsize=config['data_queue']['max_size'])
            publish_thread = Thread(
                target=publish_data,
                args=(mqtt_client, greengrass_manager, data_queue, config['mqtt']['topics']['sensor_data'], alert_manager),
                daemon=True
            )
            publish_thread.start()

            # Loop principal
            logging.info("Detectando y Procesando Datos.")
            last_diagnostics_time = time.time()
            while True:
                for sensor in sensors:
                    try:
                        mux_manager.select_channel(sensor.channel)
                        spectral_data = sensor.read_advanced_spectrum()
                        if data:
                            material = classify_material(spectral_data, config['plastic_thresholds'])
                            data_queue.put({
                                "timestamp": datetime.now().isoformat(),
                                "channel": channel,
                                "data": data,
                                "material": material,
                            })
                            logging.info(f"Canal {channel} clasificado como: {material}")
                            if material in ["PET", "HDPE"]:
                                activate_valve(material, mqtt_client)

                            logging.info(f"Material detectado: {material}.")

                    except Exception as e:
                        logging.error(f"Error procesando datos del sensor {sensor.name} en canal {channel}: {e}")
                    finally:
                        mux_manager.disable_all_channels()

                # Diagnósticos periódicos
                if time.time() % DIAGNOSTICS_INTERVAL == 0:
                    sensor_manager.perform_diagnostics()

        except Exception as e:
            logging.critical(f"Error crítico en el sistema: {e}")
            retries += 1
            if retries >= MAX_RETRIES:
                logging.critical("Se alcanzó el máximo de reinicios. Abortando.")
                sys.exit(1)
            if config['system'].get('enable_auto_restart', False):
                logging.error("Reiniciando sistema por error crítico según configuración...")
                restart_system()
            else:
                logging.error("Reinicio automático deshabilitado.")
                break
        finally:
            if network_manager:
                network_manager.stop_monitoring()
                logging.info("Monitoreo de red detenido.")
            if config_manager:
                config_manager.stop_monitoring()
                logging.info("Sistema apagado correctamente.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error crítico en la ejecución: {e}")
