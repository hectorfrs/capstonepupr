#main_pi1.py - Script principal para el Raspberry Pi 1.

# Encabezado
import sys
import os
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
    Configura el sistema de logging, con soporte para habilitar DEBUG detallado.
    """
    log_file = os.path.expanduser(config['logging']['log_file'])
    error_log_file = config['logging']['error_log_file']
    max_size = config['logging']['max_size_mb'] * 1024 * 1024
    backup_count = config['logging']['backup_count']
    detailed_logging = config['system']['enable_detailed_logging']

    if not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file))

    logging.basicConfig(
        level=logging.DEBUG if detailed_logging else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            RotatingFileHandler(log_file, maxBytes=max_size, backupCount=backup_count),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.getLogger().addHandler(logging.FileHandler(error_log_file, mode='a', level=logging.ERROR))
    sys.stdout = StreamToLogger(logging.getLogger(), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger(), logging.ERROR)

#Clasificacion y Deteccion de Plasticos
def classify_plastic(spectral_data, thresholds):
    """
    Clasifica el tipo de plástico según los umbrales configurados.
    """
    for plastic_type, ranges in thresholds.items():
        if all(ranges[i][0] <= spectral_data[i] <= ranges[i][1] for i in range(len(ranges))):
            return plastic_type
    return "Otros"

# Publicación de Datos
def publish_data(mqtt_client, greengrass_manager, topic, data_queue, alert_manager):
    """
    Publica datos encolados a MQTT y AWS IoT Core.
    """
    while True:
        try:
            data = data_queue.get(timeout=5)
            mqtt_client.publish(topic, data)
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
def run_power_saving_mode(mux_manager, sensors, enabled):
    """
    Ejecuta el modo de ahorro de energía si está habilitado.
    """
    if not enabled:
        logging.info("Modo de ahorro de energía deshabilitado.")
        return

    logging.info("Habilitando modo de ahorro de energía...")
    for sensor in sensors:
        sensor.power_off()
        logging.info(f"Sensor {sensor.name} apagado.")
    mux_manager.disable_all_channels()
    logging.info("Todos los canales desactivados.")

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
    if config['system'].get('enable_auto_restart', False):
        logging.critical("Reiniciando sistema por error crítico según configuración...")
        subprocess.run(["sudo", "reboot"])
    else:
        logging.critical("El reinicio automático está deshabilitado. Requiere intervención manual.")

# Funcion Principal
def main():
    mqtt_client, alert_manager, mux_manager, sensors = None, None, None, []

    try:
        # Cargar configuración
        config_path = "/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml"
        config_manager = RealTimeConfigManager(config_path)
        config_manager.start_monitoring()
        config = config_manager.get_config()

        # Configurar logging
        configure_logging(config)
        logging.info("Sistema iniciado en Raspberry Pi #1...")

        # Inicializar Alert Manager
        alert_manager = AlertManager(
            mqtt_client=None,
            alert_topic=config['mqtt']['topics']['alerts'],
            local_log_path=config['logging']['log_file']
        )

        # Inicializar MQTT
        mqtt_client = MQTTPublisher(config_path)
        mqtt_client.connect()

        # Inicializar MUX Manager
        mux_manager = MUXManager(
            i2c_bus=config['sensors']['as7265x']['i2c_bus'],
            i2c_address=config['mux']['i2c_address'],
            alert_manager=alert_manager
        )

        # Configurar sensores
        sensors = [
            CustomAS7265x(config_path, name=ch['sensor_name'])
            for ch in config['mux']['channels']
        ]

        # Diagnósticos
        run_diagnostics(config, mux_manager, sensors, alert_manager)

        # Modo de ahorro de energía
        run_power_saving_mode(mux_manager, sensors, config['system']['enable_power_saving'])

        # Bucle principal
        data_queue = Queue(maxsize=config['data_queue']['max_size'])
        publish_thread = Thread(target=publish_data, args=(mqtt_client, None, config['mqtt']['topics']['sensor_data'], data_queue, alert_manager), daemon=True)
        publish_thread.start()

        while True:
            for sensor in sensors:
                try:
                    spectral_data = sensor.read_advanced_spectrum()
                    plastic_type = classify_plastic(spectral_data, config['plastic_thresholds'])
                    data_queue.put({
                        "timestamp": datetime.now().isoformat(),
                        "sensor": sensor.name,
                        "data": spectral_data,
                        "plastic_type": plastic_type
                    })
                    logging.info(f"Clasificado como: {plastic_type}")
                except Exception as e:
                    logging.error(f"Error procesando sensor {sensor.name}: {e}")

    except Exception as e:
        logging.critical(f"Error crítico: {e}")
        alert_manager.send_alert(
            level="CRITICAL",
            message="Error crítico en el sistema principal",
            metadata={"error": str(e)}
        )
        # Llamar al reinicio automático si está habilitado
        restart_system(config)
    finally:
        logging.info("Sistema apagado correctamente.")
