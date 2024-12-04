import logging
import random
import time
from datetime import datetime
from threading import Thread

from utils.real_time_config import RealTimeConfigManager
from utils.mqtt_publisher import MQTTPublisher
from lib.mux_controller import MUXController
from lib.as7265x import CustomAS7265x
from lib.sensor_diagnostics import run_sensor_diagnostics
from lib.mux_diagnostics import run_mux_diagnostics

# Configuración inicial
CONFIG_PATH = "/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml"
LOG_FILE = "/logs/test_main_pi1.log"

# Configurar logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def simulate_processing(sensor_name, thresholds, max_time_ms):
    """
    Simula el tiempo de procesamiento de un sensor.
    """
    start_time = datetime.now()
    processing_time = random.randint(200, 700)  # Simula un tiempo de procesamiento aleatorio en ms

    if processing_time > max_time_ms:
        logging.warning(f"Tiempo de procesamiento del sensor {sensor_name} excedido: {processing_time} ms")
    else:
        logging.info(f"Tiempo de procesamiento del sensor {sensor_name}: {processing_time} ms")

    end_time = datetime.now()
    return (end_time - start_time).total_seconds()

def simulate_power_saving(mux, enable):
    """
    Simula el comportamiento del modo de ahorro de energía.
    """
    if enable:
        mux.disable_all_channels()
        logging.info("Modo de ahorro de energía activado. Todos los canales del MUX desactivados.")
    else:
        logging.info("Modo de ahorro de energía desactivado. MUX funcionando normalmente.")

def simulate_metrics_publishing(mqtt_client, topic, interval, stop_event):
    """
    Simula la publicación de métricas del sistema en un intervalo definido.
    """
    while not stop_event.is_set():
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": random.uniform(10, 90),  # Simula uso de CPU en porcentaje
            "memory_usage": random.uniform(20, 80),  # Simula uso de memoria en porcentaje
            "active_sensors": random.randint(1, 2)  # Número de sensores activos
        }
        mqtt_client.publish(topic, metrics)
        logging.info(f"Métricas publicadas: {metrics}")
        time.sleep(interval)

def main():
    """
    Ejecuta las pruebas de funcionalidades nuevas en Raspberry Pi 1.
    """
    # Cargar configuración
    config_manager = RealTimeConfigManager(CONFIG_PATH)
    config_manager.start_monitoring()
    config = config_manager.get_config()

    # Configurar cliente MQTT
    mqtt_client = MQTTPublisher(config_path=CONFIG_PATH, local=True)
    mqtt_client.connect()

    # Inicializar MUX
    mux = MUXController(
        i2c_bus=config['mux']['i2c_bus'],
        i2c_address=config['mux']['i2c_address']
    )

    # Inicializar Sensores
    sensors = [
        CustomAS7265x(channel_config)
        for channel_config in config['mux']['channels']
        if CustomAS7265x(channel_config).is_connected()
    ]

    # Simular diagnósticos
    if config['system'].get('enable_sensor_diagnostics', False):
        run_sensor_diagnostics(sensors)
    if config['system'].get('enable_mux_diagnostics', False):
        run_mux_diagnostics(mux)

    # Simular tiempos de procesamiento
    thresholds = config['plastic_thresholds']
    max_time_ms = config['system']['processing_time_alert_ms']
    for sensor_config in config['mux']['channels']:
        simulate_processing(sensor_config['sensor_name'], thresholds, max_time_ms)

    # Simular ahorro de energía
    if config['system']['enable_power_saving']:
        simulate_power_saving(mux, enable=True)
        time.sleep(5)
        simulate_power_saving(mux, enable=False)

    # Simular publicación de métricas
    metrics_topic = config['mqtt']['topics']['metrics']
    metrics_interval = config['system']['metrics_interval']
    stop_event = Thread.Event()
    metrics_thread = Thread(target=simulate_metrics_publishing, args=(mqtt_client, metrics_topic, metrics_interval, stop_event))
    metrics_thread.start()

    try:
        time.sleep(20)  # Ejecutar las simulaciones por 20 segundos
    finally:
        stop_event.set()
        metrics_thread.join()
        logging.info("Pruebas finalizadas.")

if __name__ == "__main__":
    main()
