# main.py - Script principal para la captura de datos de los sensores AS7265x
# Desarrollado por Héctor F. Rivera Santiago
# copyright (c) 2024

# Raspberry Pi #1 (Análisis Espectral y Clasificación del Plástico)

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
from utils.alert_manager import AlertManager    
from utils.performance_tracker import PerformanceTracker    
from utils.real_time_config import RealTimeConfigManager
from utils.config_manager import ConfigManager
from utils.logging_manager import FunctionMonitor
from utils.json_logger import log_detection

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

# Funciones auxiliares

def initialize_mux(config):
    """
    Inicializa y configura el MUX TCA9548A.
    """
    if 'mux' not in config or 'address' not in config['mux']:
        logging.error("[MAIN] [MUX] La configuración del MUX es inválida o incompleta.")
        sys.exit(1)

    mux = TCA9548A_Manager(address=config['mux']['address'])
    mux_channels = [entry['channel'] for entry in config['mux']['channels']]

    logging.info(f"[MAIN] [MUX] Habilitando canales: {mux_channels}")
    mux.enable_multiple_channels(mux_channels)
    logging.info("[MAIN] [MUX] Canales habilitados correctamente.")

    return mux

def initialize_sensors(config, mux):
    """
    Inicializa y configura los sensores AS7265x conectados al MUX.
    """
    sensors = []
    for channel_entry in config["mux"]["channels"]:
        channel = channel_entry["channel"]
        sensor_name = channel_entry["sensor_name"]

        logging.info(f"[MAIN] [SENSOR] Inicializando sensor en canal {channel}...")
        try:
            mux.enable_channel(channel)
            time.sleep(0.5)  # Esperar estabilización

            sensor = AS7265x_Manager(i2c_bus=1, address=0x49, config=config)
            sensor.reset()
            time.sleep(10)

            if not sensor.check_sensor_status():
                logging.critical("[MAIN] [SENSOR] Sensor no está listo después del reinicio.")
                continue

            sensor.initialize_sensor()
            sensors.append(sensor)
            logging.info(f"[MAIN] [SENSOR] Sensor {sensor_name} inicializado correctamente.")
        except Exception as e:
            logging.error(f"[MAIN] [SENSOR] Error al inicializar el sensor en canal {channel}: {e}")
        finally:
            mux.disable_channel(channel)

    if not sensors:
        logging.error("[MAIN] No se pudieron inicializar sensores. Finalizando...")
        sys.exit(1)

    return sensors

def initialize_components(config_path):
    """
    Inicializa y configura los componentes necesarios.

    :param config_path: Ruta al archivo de configuración.
    :return: Diccionario con las instancias inicializadas.
    """
    components = {}

    # Cargar configuración
    cconfig_manager = ConfigManager(config_path)
    #config = config_manager.config

    # Inicializar el logger
    logging.basicConfig(
        level=logging.DEBUG if config['system'].get('enable_logging') else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(config['logging']['log_file']),
            logging.StreamHandler()
        ]
    )
    logging.info("[MAIN] Sistema inicializando...")

    # Inicializar gestores
    components = {
        'network_manager': NetworkManager(config),
        'mqtt_publisher': MQTTPublisher(config),
        'alert_manager': AlertManager(mqtt_client=MQTTPublisher(config)),
        'real_time_config': RealTimeConfigManager(config_path),
        'greengrass_manager': GreengrassManager(config_path),
        'function_monitor': FunctionMonitor(config_path)
    }
    
    logging.info("[MAIN] Componentes inicializados correctamente.")
    return components, config

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

    # Inicializar componentes
    components, config = initialize_components(config_path)
    logging.debug(f"Configuración cargada: {config}")
    components['network_manager'].start_monitoring()
    components['real_time_config'].start_monitoring()
    components['function_monitor'].monitor_changes()

    # Configuración de red
    network_manager = NetworkManager(config=config_path)
    network_manager.start_monitoring()

    # Inicialización de MQTT Client
    mqtt_client = MQTTPublisher(config=config_path)
    mqtt_client.connect()

    # Escanear el bus I2C
    detected_devices = scan_i2c_bus()

    # Verificar si las direcciones esperadas están presentes
    expected_devices = [0x70, 0x49]  # Dirección del MUX y del sensor AS7265x
    for device in expected_devices:
        if device not in detected_devices:
            logging.error(f"[MAIN] [SCAN] Dispositivo con dirección {hex(device)} no encontrado.")
        else:
            logging.info(f"[MAIN] [SCAN] Dispositivo con dirección {hex(device)} detectado correctamente.")
    
    # Inicializar MUX
    logging.info("[MAIN] [MUX] Inicializando...")
    if 'mux' not in config or 'address' not in config['mux']:
        logging.error("[MAIN] [MUX] La configuración del MUX es inválida o incompleta.")
        sys.exit(1)
    mux = initialize_mux(config)
    sensors = initialize_sensors(config, mux)

    # Habilitar canales del MUX
    logging.info("[MAIN] [MUX] Habilitando canales...")
    mux_channels = [entry['channel'] for entry in config['mux']['channels']]
    logging.info(f"[MAIN] [MUX] Intentando habilitar canales: {mux_channels}")
    mux.enable_multiple_channels(mux_channels)
    logging.info(f"[MAIN] [MUX] Canales habilitados correctamente.")

    # Inicializar sensores en los canales
    logging.info("[MAIN] [SENSOR] Inicializando...")
    sensors = initialize_sensors(config, mux)


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
    monitor.stop()
    

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"[MAIN] Error crítico en la ejecución principal: {e}", exc_info=True)
