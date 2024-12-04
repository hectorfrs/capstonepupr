
import sys
import os
import yaml
import time
import logging

from threading import Thread
from queue import Queue
from datetime import datetime
from datetime import timedelta
from asyncio import Handle

from lib.mux_manager import MUXManager
from lib.as7265x import CustomAS7265x
from utils.mqtt_publisher import MQTTPublisher
from utils.greengrass import GreengrassManager
from utils.network_manager import NetworkManager
from utils.json_manager import generate_json, save_json
from utils.json_logger import log_detection
from utils.real_time_config import RealTimeConfigManager
from utils.alert_manager import AlertManager
from lib.sensor_diagnostics import run_sensor_diagnostics
from lib.mux_diagnostics import run_mux_diagnostics

from logging.handlers import RotatingFileHandler

# Agregar la ruta del proyecto al PYTHONPATH
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

class PerformanceTracker:
    """
    Clase para rastrear estadísticas de rendimiento y procesamiento.
    """
    def __init__(self):
        self.total_processing_time = timedelta()
        self.num_readings = 0

    def add_reading(self, processing_time):
        self.total_processing_time += timedelta(milliseconds=processing_time)
        self.num_readings += 1

    def get_average_time(self):
        if self.num_readings == 0:
            return None
        return self.total_processing_time / self.num_readings

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
    # simulated_spectral_data = {
    #     "channel_1": 150,
    #     "channel_2": 180,
    #     "channel_3": 100
    # }

    # Comparar datos simulados con umbrales configurados
    # detected_material = "Otros"                                     # Valor predeterminado
    # confidence = 0.0

    for material, thresholds in config["plastic_thresholds"].items():
        matches = all(
            thresholds[i][0] <= spectral_data[f"channel_{i+1}"] <= thresholds[i][1]
            for i in range(len(thresholds))
        )
        if matches:
            detected_material = material
            confidence = 0.95                                       # Simula confianza máxima (puede calcularse dinámicamente)
            break

    detection_data = {
        "material": detected_material,
        "confidence": confidence,
        "spectral_data": simulated_spectral_data,
        "sensor_id": config["mux"]["channels"][0]["sensor_name"],   # Primer sensor del MUX
        "mux_channel": config["mux"]["channels"][0]["channel"],     # Canal del MUX
        "timestamp": datetime.now().isoformat(),
        "processing_time_ms": 120,                                  # Simulado
        "device_id": config["network"]["ethernet"]["ip"],           # Dirección IP del dispositivo
        "location": "line_1_zone_A"                                 # Estático, puedes actualizar si es dinámico
    }

    return detection_data



def configure_logging(config):
    """
    Configura el sistema de logging.
    """
    log_file = os.path.expanduser(config['logging']['log_file'])    
    log_dir = os.path.dirname(log_file)

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        filename=log_file,                                          # Archivo de log especificado en config.yaml
        level=logging.INFO,                                         # Nivel de logging (puedes usar DEBUG, INFO, WARNING, etc.)
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",                                # Formato de la fecha y hora
    )

    error_log_file = config["logging"]["error_log_file"]
    max_log_size = config.get("logging", {}).get("max_size_mb", 5) * 1024 * 1024  # Tamaño máximo en bytes
    backup_count = config.get("logging", {}).get("backup_count", 3)  # Número de archivos de respaldo

    # Configuración del RotatingFileHandler
    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=max_log_size,  # Tamaño máximo del archivo en bytes
        backupCount=backup_count,  # Número de archivos de respaldo
    )
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    # Configuración del manejador para logs de errores
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # Agregar manejadores al logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(error_handler)

    print(f"Logging configurado en {log_file}.")

    # Redirigir stdout y stderr al logger después de configurarlo
    sys.stdout = StreamToLogger(logging.getLogger(), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger(), logging.ERROR)

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
        # Seleccionar canal
        mux_manager.select_channel(channel)

        # Reiniciar canal en caso de error
        mux_manager.reset_channel(channel)

        # Seleccionar canal en el MUX
        mux.select_channel(channel)
        logging.info(f"Canal {channel} activado para el sensor {sensor_name}.")
        
        # Leer datos espectrales del sensor
        spectral_data = sensor.read_advanced_spectrum()
        logging.info(f"Datos leídos del sensor {sensor_name}: {spectral_data}")

        # Identificar material
        detected_material = identify_plastic(spectral_data, thresholds)
        logging.info(f"Material detectado por {sensor_name}: {detected_material}")

        # Crear payload para publicación
        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sensor": sensor_name,
            "material": detected_material,
            **spectral_data
        }

        # Encolar datos para publicación
        data_queue.put(payload, timeout=1)
        logging.info(f"Datos encolados para publicación: {payload}")

    except queue.Full:
        logging.error(f"La cola de datos está llena. Datos del sensor {sensor_name} descartados.")
    except Exception as e:
        alert_manager.send_alert(
            level="CRITICAL",
            message=f"Error procesando el sensor {sensor_name} en el canal {channel}: {e}",
            metadata={"sensor": sensor_name, "channel": channel},
        )
    finally:
        # Limpieza o reinicio del MUX en caso de error
        mux.reset_channel(channel)
        try:
            mux.disable_all_channels()
        except Exception as e:
            logging.warning(f"Error limpiando el canal {channel}: {e}")


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
            alert_manager.send_alert(
                level="CRITICAL",
                message=f"Error publicando datos al MQTT: {e}",
                metadata={"topic": topic},
            )

def run_diagnostics(config, mux, sensors):
    """
    Ejecuta diagnósticos de sensores y MUX según la configuración.
    """
    if config['system'].get('enable_sensor_diagnostics', False):
        from lib.sensor_diagnostics import run_sensor_diagnostics
        run_sensor_diagnostics(sensors)

    if config['system'].get('enable_mux_diagnostics', False):
        from lib.mux_diagnostics import run_mux_diagnostics
        run_mux_diagnostics(mux)

def run_power_saving_mode(mux, sensors):
    """
    Habilita el modo de ahorro de energía apagando sensores y canales no críticos.
    """
    logging.info("Entrando en modo de ahorro de energía...")
    for sensor in sensors:
        if not sensor.is_critical():
            sensor.power_off()
            logging.info(f"Sensor {sensor.name} apagado para ahorrar energía.")
    mux.disable_all_channels()
    logging.info("Todos los canales del MUX han sido desactivados.")

        

def main():
    """
    Función principal para manejar la lógica del Raspberry Pi 1.
    """
    # Inicializa la gestión de configuración en tiempo real
    config_path = "/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml"
    config_manager = RealTimeConfigManager(config_path)
    config_manager.start_monitoring()

    try:
        # Usar configuración actualizada
        config = config_manager.get_config()

        # Configurar logging
        configure_logging(config)
        logging.info("Sistema iniciado en Raspberry Pi #1.")

        # Configurar red y monitoreo
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()
        alert_manager.send_alert(
            level="CRITICAL",
            message="No hay conexión a Internet.",
            metadata={"ethernet_ip": config['network']['ethernet']['ip']}
        )

        # Inicializar cliente MQTT
        logging.info("Inicializando cliente MQTT...")
        mqtt_client = MQTTPublisher(config_path=config_manager.config_path, local=True)
        mqtt_client.connect()

        # Inicializar Greengrass Manager
        greengrass_manager = GreengrassManager(config_path=config_manager.config_path)

        # Inicializar Alert Manager
        alert_manager = AlertManager(mqtt_client=mqtt_client, alert_topic=config['mqtt']['topics']['alerts'])

        # Inicializar MUX
        logging.info("Inicializando MUX...")
        mux_manager = MUXManager(
            i2c_bus=config['sensors']['as7265x']['i2c_bus'],
            i2c_address=config['mux']['i2c_address'],
            alert_manager=alert_manager
        )

        # Inicializar Sensores
        sensors_config = config['mux']['channels']
        sensors = [
            CustomAS7265x(config_path=config_manager.config_path)
            for sensor_config in sensors_config
            if CustomAS7265x(config_path=config_manager.config_path).is_connected()
        ]
        
        # Manejo de sensores conectados
        if not sensors:
            alert_manager.send_alert(
                level="CRITICAL",
                message="No se detectaron sensores conectados.",
                metadata={"mux_address": config['mux']['i2c_address']},
            )
            raise RuntimeError("No se detectaron sensores conectados. Terminando el programa.")
        
        # Diagnósticos de sensores
        if config['system'].get('enable_sensor_diagnostics', False):
            logging.info("Ejecutando diagnósticos de sensores...")
            run_sensor_diagnostics(sensors, alert_manager)

        # Diagnósticos de MUX
        if config['system'].get('enable_mux_diagnostics', False):
            logging.info("Ejecutando diagnósticos del MUX...")
            run_mux_diagnostics(mux, [ch['channel'] for ch in config['mux']['channels']], alert_manager)

        logging.info(f"{len(sensors)} sensores configurados con éxito.")

        # Configurar Buffer de Datos
        data_queue = Queue(maxsize=config['data_queue']['max_size'])
        logging.info(f"Queue de datos inicializada con tamaño máximo: {config['data_queue']['max_size']}")

        # Inicializar Traker de Performance
        performance_tracker = PerformanceTracker()
        last_metrics_publish_time = time.time()
        METRICS_INTERVAL = config['system'].get('metrics_interval', 60)  # Intervalo en segundos

        # Hilo para Publicar Datos
        publish_thread = Thread(
            target=publish_data,
            args=(mqtt_client, greengrass_manager, config['mqtt']['topics']['sensor_data'], data_queue),
            daemon=True
        )
        publish_thread.start()

        mux_status = mux_manager.get_status()
        logging.info(f"Estado inicial del MUX: {mux_status}")

        # Loop Principal
        while True:
            for sensor_idx, sensor_config in enumerate(sensors_config):
                process_sensor(
                    mux=mux,
                    sensor=sensors[sensor_idx],
                    channel=sensor_config['channel'],
                    sensor_name=sensor_config['sensor_name'],
                    thresholds=config['plastic_thresholds'],
                    data_queue=data_queue,
                    alert_manager=alert_manager,
                )
            time.sleep(config['sensors']['read_interval'])

            try:
                start_time = time.time()
                process_sensor(...)  # Llamada existente a la función
                processing_time = (time.time() - start_time) * 1000  # Milisegundos
                performance_tracker.add_reading(processing_time)
                logging.info(f"Tiempo de procesamiento: {processing_time:.2f} ms")
            except Exception as e:
                logging.error(f"Error durante el procesamiento: {e}")

            # Publicar métricas periódicamente
            if time.time() - last_metrics_publish_time > METRICS_INTERVAL:
                average_time = performance_tracker.get_average_time()
                if average_time:
                    metrics_payload = {
                        "average_processing_time_ms": average_time.total_seconds() * 1000,
                        "total_readings": performance_tracker.num_readings
                    }
                    mqtt_client.publish("pi1/performance_metrics", json.dumps(metrics_payload))
                    logging.info(f"Métricas publicadas: {metrics_payload}")
                last_metrics_publish_time = time.time()

                # Ahorro de energía
            run_power_saving_mode(config, mux, sensors)
                
    except Exception as e:
        alert_manager.send_alert(
            level="CRITICAL",
            message="Error en el loop principal",
            metadata={"error": str(e)}
    )
    
    except KeyboardInterrupt:
        logging.info("Programa detenido por el usuario.")
    except Exception as e:
        logging.critical(f"Error crítico en el sistema: {e}")
        if 'alert_manager' in locals():
            alert_manager.send_alert("CRITICAL", f"Error crítico en el sistema: {e}")
    finally:
        network_manager.stop_monitoring()
        config_manager.stop_monitoring()
        mqtt_client.disconnect()
        logging.info("Sistema apagado correctamente.")

if __name__ == "__main__":
    main()