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
from lib.mux_manager import MUXManager, MUXConfig
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
from utils.config_manager import ConfigManager

# Agregar la ruta del proyecto al PYTHONPATH
#print(sys.path)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append("/usr/local/lib/python3.11/dist-packages")

# Configuración de constantes
MAX_RETRIES = 3
DIAGNOSTICS_INTERVAL = 300
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
        'sensors': ['as7265x', 'default_settings'],
        'mqtt': ['topics'],
        'logging': ['log_file', 'error_log_file'],
        'network': ['ethernet'],
        'system': ['enable_detailed_logging', 'enable_auto_restart', 'enable_power_saving']
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
            if isinstance(data, dict):
                raise ValueError("Formato de datos incorrecto.")
            # Publicar datos en MQTT Localmente
            mqtt_client.publish(topic, data)
            logging.info(f"Datos publicados en MQTT: {data}")
            
            # Publicar datos en AWS IoT Core
            response = greengrass_manager.invoke_function(data)
            logging.info(f"Datos publicados en MQTT y procesados por Greengrass: {data} | Respuesta: {response}")
        except ValueError as ve:
            logging.error(f"Error en los datos: {ve}")
        except Exception as e:
            logging.error(f"Error publicando datos: {e}")
            alert_manager.send_alert(
                level="CRITICAL",
                message="Error al publicar datos",
                metadata={"error": str(e)}
            )

# Ahorro de energia
def run_power_saving_mode(sensors, mux_manager, enabled):
    if not enabled:
        logging.info("Modo de ahorro de energía deshabilitado.")
        return

    logging.info("Habilitando modo de ahorro de energía...")
    try:
        if not sensors:
            logging.info("No hay sensores para apagar.")
        else:
            for sensor in sensors:
                sensor.power_off()
                logging.info(f"Sensor {sensor.name} apagado para ahorro de energía.")

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
        run_mux_diagnostics(mux_manager, [ch['id'] for ch in config['mux']['channels']], alert_manager)

def diagnostics_loop(config, mux_manager, sensors, alert_manager):
     while True:
        try:
            run_diagnostics(config, mux_manager, sensors, alert_manager)
            time.sleep(config["system"]["diagnostics_interval"])
        except Exception as e:
            logging.error(f"Error en el loop de diagnósticos: {e}")
            break

# Reinicio Automatico
def restart_system(config):
    """
    Reinicia el sistema en caso de falla crítica si está habilitado en el config.yaml.
    """
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
        channels = [ch["id"] for ch in config["mux"]["channels"]]
        mux_config = MUXConfig(**config['mux'])
        i2c_address = int(config['mux']['i2c_address'], 16) if isinstance(config['mux']['i2c_address'], str) else config['mux']['i2c_address']
        mux_manager = MUXManager(
            i2c_bus=config['mux']['i2c_bus'],
            i2c_address=i2c_address,
            alert_manager=alert_manager
        )

        mux_manager.initialize_channels(channels)
        logging.info(f"MUX inicializado con canales: {channels}")

        if not mux_manager.is_mux_connected():
            raise RuntimeError("MUX no conectado o no accesible.")
        logging.info("MUX inicializado correctamente.")
        mux_status = mux_manager.get_status()
        return mux_manager
    except Exception as e:
        logging.critical(f"Error inicializando el MUX: {e}", exc_info=True)
        alert_manager.send_alert(
            level="CRITICAL",
            message="Error inicializando el MUX.",
            metadata={"error": str(e)}
        )
        raise



# Inicialización de Sensores
def init_sensors(config, mux_manager, alert_manager):
    try:
        sensor_manager = initialize_sensors(config, mux_manager, alert_manager)
    except Exception as e:
        logging.critical("Error al inicializar los sensores. El sistema se detendrá.{e}", exc_info=True)
        sys.exit(1)

# def process_channels(mux_manager):
#     try:
#         active_channels = mux_manager.detect_active_channels()
#         for channel in active_channels:
#             try:
#                 mux_manager.activate_channel(channel)
#                 logging.info(f"Canal {channel} activado.")
#                 # Otras operaciones aquí
#             finally:
#                 mux_manager.deactivate_channel(channel)
#     except Exception as e:
#         logging.error(f"Error procesando canales del MUX: {e}")

def process_sensor(sensor, channel, mux_manager, alert_manager, id):
    """
    Procesa un sensor específico, validando su estado antes de realizar operaciones.
    """
    try:
        if not sensor.is_connected():
            raise RuntimeError(f"Sensor {sensor.name} no conectado.")
        
        if sensor.is_powered_off():
            raise RuntimeError(f"Sensor {sensor.name} está apagado. No se puede leer datos.")

        mux_manager.select_channel(id)
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

def main():
    """
    Función principal del sistema.
    """
    print("Iniciando Sistema...")
    retries = 0
    config_manager = None
    mqtt_client = None
    network_manager = None
    alert_manager = None
    mux_manager = None
    sensors = []
    last_diagnostics_time = time.time()
    config_path = "/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml"
    
    while retries < MAX_RETRIES:
        try:
            # Cargar configuración
            config_path = "/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml"
            config_manager = RealTimeConfigManager(config_path)
            config_manager.start_monitoring()
            config = config_manager.get_config()
            validate_config(config)

            #  # Usa la configuración cargada
            # MAX_RETRIES = config["system"]["max_retries"]
            # DIAGNOSTICS_INTERVAL = config["system"]["diagnostics_interval"]

            # # Resto de tu inicialización y lógica principal...
            # logging.info(f"MAX_RETRIES: {MAX_RETRIES}, DIAGNOSTICS_INTERVAL: {DIAGNOSTICS_INTERVAL}")

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
            network_manager = NetworkManager(config)
            network_manager.start_monitoring()
            
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

            # Detectar y Actualizar Canales Activos
            try:
                channels = [ch["id"] for ch in config["mux"]["channels"]]
                mux_manager.initialize_channels(channels)

                #config_manager.set_value('mux', 'active_channels', active_channels)
                #logging.info(f"Canales activos detectados y actualizados: {active_channels}")
            except Exception as e:
                logging.critical(f"Error detectando canales activos: {e}")
                alert_manager.send_alert(
                    level="CRITICAL",
                    message="Error detectando canales activos",
                    metadata={"error": str(e)},
                )
                raise RuntimeError("Error detectando canales activos")

            # Diagnósticos iniciales
            run_diagnostics(config, mux_manager, sensors, alert_manager)

            # Inicializar Greengrass Manager
            logging.info("Inicializando Greengrass Manager...")
            greengrass_manager = GreengrassManager(config_path=config_manager.config_path)

            # Inicializar sensores
            logging.info("Inicializando sensores...")
            sensor_manager = init_sensors(config, mux_manager)
            # Leer datos de sensores en paralelo
            sensor_manager.read_sensors_concurrently()

            # Ejecutar diagnósticos iniciales de sensores
            logging.info("Ejecutando diagnósticos iniciales de sensores...")
            diagnostics = run_sensor_diagnostics(sensor_manager.sensors, alert_manager)

            if not diagnostics:
                logging.warning("Los diagnósticos no devolvieron resultados.")
            else:
                logging.info(f"Resultados del diagnóstico inicial: {diagnostics}")
                for sensor_name, result in diagnostics.items():
                    if result.get("status") != "OK":
                        logging.warning(f"Sensor {sensor_name} requiere atención: {result}")
            
            # Verificar si el resultado es None
            if diagnostics is None:
                diagnostics = {}  # Reemplazar con un diccionario vacío
                logging.error("Diagnósticos retornaron None. Ajustando a un diccionario vacío.")


            # Reaccionar ante sensores no operativos
            for sensor_name, result in diagnostics.items():
                if result.get("connected") is False or result.get("status") == "ERROR":
                    logging.warning(f"El sensor {sensor_name} requiere atención.")

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
            while True:
                current_time = time.time()
                for sensor in sensors:
                    try:
                        mux_manager.select_channel(sensor.channel)
                        spectral_data = sensor.read_advanced_spectrum()
                        if spectral_data:
                            material = classify_material(spectral_data, config['plastic_thresholds'])
                            data_queue.put({
                                "timestamp": datetime.now().isoformat(),
                                "channel": sensor.channel,
                                "data": spectral_data,
                                "material": material,
                            })
                            logging.info(f"Canal {sensor.channel} clasificado como: {material}")
                            if material in ["PET", "HDPE"]:
                                activate_valve(material, mqtt_client)

                            logging.info(f"Material detectado: {material}.")

                    except Exception as e:
                        logging.error(f"Error procesando datos del sensor {sensor.name} en canal {sensor.channel}: {e}")
                    finally:
                        mux_manager.disable_all_channels()

                # Diagnósticos periódicos
                if current_time - last_diagnostics_time >= DIAGNOSTICS_INTERVAL:
                    run_diagnostics(config, mux_manager, sensors, alert_manager)
                    last_diagnostics_time = current_time

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
