# main.py - Script principal para la captura de datos de los sensores AS7265x
# Desarrollado por Héctor F. Rivera Santiago
# copyright (c) 2024

import logging
import yaml
import qwiic
import time
import sys
import os
#from colorlog import ColoredFormatter

# Importar módulos criticos
from lib.TCA9548A_HighLevel import TCA9548A_Manager
from lib.AS7265x_HighLevel import AS7265x_Manager
from lib.AS7265x_HighLevel import generate_summary
from utils.process_manager import process_individual, process_with_conveyor

# Importar módulos personalizados
from utils.mqtt_publisher import MQTTPublisher
from utils.greengrass import GreengrassManager
from utils.network_manager import NetworkManager
from utils.json_logger import log_detection
from utils.alert_manager import AlertManager
from utils.performance_tracker import PerformanceTracker
from utils.real_time_config import RealTimeConfigManager
from utils.config_manager import ConfigManager

try:
    from qwiic import QwiicKx13X, QwiicAs6212
except ImportError:
    print("QwiicKx13X y QwiicAs6212 no están disponibles. Ignorando...")

try:
    import spidev
except ImportError:
    print("El módulo spidev no está disponible. Ignorando...")

# Agregar la ruta del proyecto al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Cargar configuración desde el archivo config.yaml

def load_config(config_path):
    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
            if not config:
                raise ValueError(f"El archivo de configuración está vacío: {config_path}")
            return config
    except FileNotFoundError:
        logging.error(f"Archivo de configuración no encontrado: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error al analizar el archivo YAML: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error inesperado al cargar la configuración: {e}")
        sys.exit(1)

# Configuración de los logs
import logging
from logging.handlers import RotatingFileHandler

def configure_logging(config):
    """
    Configura el sistema de logging.
    """
    log_file = os.path.expanduser(config['logging']['log_file'])
    log_dir = os.path.dirname(log_file)
    error_log_file = config['logging']['error_log_file']
    max_log_size = config.get("logging", {}).get("max_size_mb", 5) * 1024 * 1024
    backup_count = config.get("logging", {}).get("backup_count", 3)

    # Crear directorio de logs si no existe
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configuración del logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if config.get('system', {}).get('enable_detailed_logging', False) else logging.INFO)

    # Formato de los logs
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Manejador de archivo (RotatingFileHandler)
    file_handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=backup_count)
    file_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
    file_handler.setLevel(logging.DEBUG if config.get('system', {}).get('enable_detailed_logging', False) else logging.INFO)
    logger.addHandler(file_handler)

    # Manejador de consola (StreamHandler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
    console_handler.setLevel(logging.DEBUG if config.get('system', {}).get('enable_detailed_logging', False) else logging.INFO)
    logger.addHandler(console_handler)

    # Manejador de errores
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

    logging.info("Sistema de logging configurado correctamente.")


def scan_i2c_bus():
    """
    Escanea el bus I2C y devuelve una lista de dispositivos detectados.
    """
    devices = qwiic.scan()
    if devices:
        logging.info(f"[SCAN] Dispositivos detectados en el bus I2C: {[hex(addr) for addr in devices]}")
    else:
        logging.warning("[SCAN] No se detectaron dispositivos en el bus I2C.")
    return devices

# Función principal
def main():
    print("===============================================")
    print("        Iniciando Sistema de Acopio...")
    print("===============================================")
    
    # Variables de estado
    successful_reads = 0
    failed_reads = 0
    error_details = []

    # Cargar configuración
    config_path = "/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config_optimized.yaml"
    config = load_config(config_path)
    required_keys = ['mux', 'sensors', 'system']
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        logging.error(f"Faltan claves requeridas en la configuración: {missing_keys}")
        sys.exit(1)

    # Configuración de logging
    configure_logging(config)
    logging.info("=" * 50)
    logging.info("[MAIN] Sistema iniciado en Raspberry Pi #1...")
    logging.info("[MAIN] Análisis Espectral y Clasificación del Plástico.")
    logging.info("=" * 50)

    # Configuración de red
    network_manager = NetworkManager(config)
    network_manager.start_monitoring()

    # Inicialización de MQTT Client
    mqtt_client = MQTTPublisher(config)
    mqtt_client.connect()

    # Escanear el bus I2C
    detected_devices = scan_i2c_bus()

    # Verificar si las direcciones esperadas están presentes
    expected_devices = [0x70, 0x49]  # Dirección del MUX y del sensor AS7265x
    for device in expected_devices:
        if device not in detected_devices:
            logging.error(f"[SCAN] Dispositivo con dirección {hex(device)} no encontrado.")
        else:
            logging.info(f"[SCAN] Dispositivo con dirección {hex(device)} detectado correctamente.")
    
    # Inicializar MUX
    logging.info("[MAIN] [MUX] Inicializando...")
    if 'mux' not in config or 'address' not in config['mux']:
        logging.error("[MAIN] [MUX] La configuración del MUX es inválida o incompleta.")
        sys.exit(1)
    mux = TCA9548A_Manager(address=config['mux']['address'])

    # Habilitar canales del MUX
    logging.info("[MAIN] [MUX] Habilitando canales...")
    mux_channels = [entry['channel'] for entry in config['mux']['channels']]
    logging.info(f"[MAIN] [MUX] Intentando habilitar canales: {mux_channels}")
    mux.enable_multiple_channels(mux_channels)
    logging.info(f"[MAIN] [MUX] Canales habilitados correctamente.")

    # Inicializar sensores en los canales
    logging.info("[MAIN] [SENSOR] Inicializando...")
    sensors = []

    for channel_entry in config["mux"]["channels"]:
        channel = channel_entry["channel"]
        sensor_name = channel_entry["sensor_name"]

        
        logging.info("=" * 50)
        logging.info(f"[MAIN] [SENSOR] Inicializando sensor en canal {channel}...")
        try:
            logging.debug(f"[MAIN] [MUX] Habilitando canal {channel}.")
            mux.enable_channel(channel)
            logging.info(
                f"[MAIN] [MUX] El canal {channel} ha sido habilitado. "
                f"Esperando estabilización del sensor..."
                )
            time.sleep(0.5)    # esperar a que el sensor se estabilice
            logging.debug(f"[MAIN] [MUX] Canal {channel} habilitado.")
        
            # Crea instancia High Level para el sensor
            sensor = AS7265x_Manager(i2c_bus=1, address=0x49, config=config)
            sensor.reset()
            time.sleep(5)  # Esperar después del reset.
            
            # Leer el estado del sensor desde el Manager
            try:
                if not sensor.check_sensor_status():
                    raise Exception("[MAIN] [SENSOR] El sensor no está listo después del reinicio.")

                sensor.initialize_sensor()
                logging.info(f"[MAIN] [SENSOR] Sensor en canal {channel} inicializado correctamente.")

                sensors.append(sensor)
            except RuntimeError as e:
                logging.error(f"[MAIN] [SENSOR] Error al verificar el estado del sensor: {e}")
                continue
            logging.info(f"[MAIN] [SENSOR] Sensor {sensor_name} inicializado y configurado correctamente.")

        except Exception as e:
            logging.error(f"[MAIN] [SENSOR] Error al configurar el sensor: {e}")
            continue
            
            # logging.info(
            #     f"[CANAL {channel} Sensor configurado: {sensor_name}] "
            #     f"Integración={integration_time}ms, Ganancia={gain}x, Modo={mode}."
            #    )

            # Deshabilitar todos los canales después de configurar el sensor
        except Exception as e:
            logging.error(f"[MAIN] [SENSOR] Error con el sensor en canal {channel}: {e}")
            continue
        finally:
            # Deshabilitar todos los canales después de configurar el sensor
            mux.disable_all_channels()
            logging.info(f"[MAIN] [MUX] Canal {channel} deshabilitado después de inicialización.")
            logging.info("=" * 50)

     # Seleccionar flujo según configuración
    if not sensors:
        logging.error("[MAIN] No se pudieron inicializar sensores. Finalizando...")
        sys.exit(1)
    system_config = config.get("system", {})
    if config["system"].get("process_with_conveyor", False):
        successful_reads, failed_reads, error_details = process_with_conveyor(config, sensors, mux)
    else:
        successful_reads, failed_reads, error_details = process_individual(config, sensors, mux)

    generate_summary(successful_reads, failed_reads, error_details)
    

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Error crítico en la ejecución principal: {e}", exc_info=True)
