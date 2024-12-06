#main_pi1.py - Script principal para el Raspberry Pi 1.
import sys
import os
import yaml
import time
import logging
import json

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
from utils.performance_tracker import PerformanceTracker
from lib.sensor_diagnostics import run_sensor_diagnostics
from lib.mux_diagnostics import run_mux_diagnostics

from logging.handlers import RotatingFileHandler

# Agregar la ruta del proyecto al PYTHONPATH
print(sys.path)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append("/usr/local/lib/python3.11/dist-packages")

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
    error_log_file = config["logging"]["error_log_file"]
    max_log_size = config.get("logging", {}).get("max_size_mb", 5) * 1024 * 1024  # Tamaño máximo en bytes
    backup_count = config.get("logging", {}).get("backup_count", 3)  # Número de archivos de respaldo

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    # Configuración del formato de los logs
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        filename=log_file,                                          # Archivo de log especificado en config.yaml
        level=logging.INFO,                                         # Nivel de logging (puedes usar DEBUG, INFO, WARNING, etc.)
        format=LOG_FORMAT,                                          # Formato del log
        datefmt="%Y-%m-%d %H:%M:%S",                                # Formato de la fecha y hora
    )

    
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

    # Redirigir stdout y stderr al logger después de configurarlo
    sys.stdout = StreamToLogger(logging.getLogger(), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger(), logging.ERROR)

    print(f"Logging configurado en {log_file}.")

    

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


def process_sensor(mux_manager, sensor, channel, sensor_name, thresholds, data_queue, alert_manager):
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
        mux_manager.select_channel(channel)
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

        if data_queue.full():
            logging.error(f"La cola de datos está llena. Datos del sensor {sensor_name} descartados.")
        else:
            data_queue.put(payload)
            logging.info(f"Datos encolados para publicación: {payload}")
    except Exception as e:
        logging.error(f"Error procesando el sensor {sensor_name}: {e}")
        if alert_manager:
            alert_manager.send_alert(
                level="WARNING",
                message=f"Error procesando el sensor {sensor_name}.",
                metadata={"sensor": sensor_name, "error": str(e)}
            )
    finally:
        # Limpieza o reinicio del MUX en caso de error
        mux_manager.reset_channel(channel)
        try:
            mux_manager.disable_all_channels()
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
                metadata={"topic": {topic}},
            )

def run_power_saving_mode(mux_manager, sensors):
    """
    Habilita el modo de ahorro de energía apagando sensores y canales no críticos.
    """
    logging.info("Entrando en modo de ahorro de energía...")
    for sensor in sensors:
        if not sensor.is_critical():  # Usamos el nuevo método aquí
            sensor.power_off()
            logging.info(f"Sensor {sensor.name} apagado para ahorrar energía.")
    mux_manager.disable_all_channels()
    logging.info("Todos los canales del MUX han sido desactivados.")

def main():
    """
    Función principal para manejar la lógica del Raspberry Pi 1.
    """

    mqtt_client = None      # Inicialización temprana
    network_manager = None  # Inicialización temprana
    alert_manager = None    # Inicialización temprana
    mux_manager = None      # Inicialización temprana
    sensors = []            # Inicialización temprana

    # Inicializa la gestión de configuración en tiempo real
    config_path = "/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config.yaml"
    config_manager = RealTimeConfigManager(config_path)
    config_manager.start_monitoring()

    # Usar configuración actualizada
    config = config_manager.get_config()

    # Configurar logging
    configure_logging(config)
    logging.debug("Sistema iniciado en Raspberry Pi #1.")
    

    try:
        

        # Inicializar Alert Manager (temprano, sin depender de otros servicios)
        alert_manager = AlertManager(
            alert_topic=config.get('mqtt', {}).get('topics', {}).get('alerts', 'raspberry-1/alerts'),
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
        
        # Inicializar cliente MQTT
        logging.info("Inicializando cliente MQTT...")
        mqtt_client = MQTTPublisher(config_path=config_manager.config_path, local=True)
        mqtt_client.connect()

        # Actualizar Alert Manager con soporte MQTT
        alert_manager = AlertManager(
            mqtt_client=mqtt_client,
            alert_topic=config['mqtt']['topics']['alerts'],
            local_log_path=config['logging']['log_file']
        )
        # Inicializar MUX
        logging.info("Inicializando MUX...")
        mux_manager = MUXManager(
            i2c_bus=config['sensors']['as7265x']['i2c_bus'],
            i2c_address=config['mux']['i2c_address'],
            alert_manager=alert_manager
        )
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
        greengrass_manager = GreengrassManager(config_path=config_manager.config_path)

        

        # Inicialización de sensores
        sensors = []  # Reinicia la lista de sensores
        sensors_config = config['mux']['channels']  # Carga la configuración de canales

        for channel_info in sensors_config:
            channel = channel_info['channel']
            sensor_name = channel_info['sensor_name']
            sensor = CustomAS7265x(config_path=config_manager.config_path, name=sensor_name)

            if sensor.is_connected():
                sensors.append({"channel": channel, "sensor": sensor})  # Guarda el sensor y su canal
                logging.info(f"Sensor {sensor_name} conectado en canal {channel}.")
            else:
                logging.warning(f"No se pudo conectar el sensor {sensor_name} en canal {channel}.")
        
            
        if not sensors:
            raise RuntimeError("No se detectaron sensores conectados. Terminando el programa.")
        
        
        # Diagnósticos de sensores
        if config['system'].get('enable_sensor_diagnostics', False):
            logging.info("Ejecutando diagnósticos de sensores...")
            for sensor in sensors:
                try:
                    temperature_c = sensor.read_temperature()
                    temperature_f = (temperature_c * 9 / 5) + 32
                    logging.info(f"Temperatura del sensor {sensor.name}: {temperature_c:.2f} °C / {temperature_f:.2f} °F")
                except AttributeError:
                    logging.error(f"El sensor {sensor.name} no soporta la lectura de temperatura.")
                except Exception as e:
                    logging.error(f"Error al diagnosticar el sensor {sensor.name}: {e}")
                    alert_manager.send_alert(
                        level="CRITICAL",
                        message=f"Error al diagnosticar el sensor {sensor.name}: {e}",
                        metadata={"sensor": sensor.name},
                    )

        # Diagnósticos de MUX
        if config['system'].get('enable_mux_diagnostics', False):
            logging.info("Ejecutando diagnósticos del MUX...")
            run_mux_diagnostics(
                mux_manager=mux_manager,
                channels=[ch['channel'] for ch in config['mux']['channels']],
                alert_manager=alert_manager
            )

        logging.info(f"{len(sensors)} sensores configurados con éxito.")

        # Inicializar Traker de Performance
        log_interval = config.get('system', {}).get('metrics_interval', 60)  # 60 es el valor por defecto
        performance_tracker = PerformanceTracker(log_interval=log_interval)

        # Configurar Buffer de Datos
        data_queue = Queue(maxsize=config['data_queue']['max_size'])
        logging.info(f"Queue de datos inicializada con tamaño máximo: {config['data_queue']['max_size']}")

        # Hilo para Publicar Datos
        publish_thread = Thread(
            target=publish_data,
            args=(mqtt_client, greengrass_manager, config['mqtt']['topics']['sensor_data'], data_queue),
            daemon=True
        )
        publish_thread.start()

        mux_status = mux_manager.detect_active_channels()
        logging.info(f"Estado inicial del MUX: {mux_status}")

        logging.info("Sistema funcionando correctamente.")

        # Loop Principal
        last_metrics_publish_time = time.time()
        METRICS_INTERVAL = log_interval  # Usar el intervalo configurado

        while True:
            for sensor_entry in sensors:
                channel = sensor_entry['channel']
                sensor = sensor_entry['sensor']
                
                try:
                    mux_manager.activate_channel(channel)  # Activa el canal correcto
                    data = sensor.read_advanced_spectrum()  # Lee los datos del sensor
                    logging.info(f"Datos del sensor {sensor.name} en canal {channel}: {data}")
                except Exception as e:
                    logging.error(f"Error procesando el sensor {sensor.name} en canal {channel}: {e}")
                finally:
                    mux_manager.deactivate_all_channels()  # Desactiva los canales para evitar conflictos
            for sensor_idx, sensor_config in enumerate(sensors_config):
                if sensor_idx < len(sensors):
                    if sensor.is_critical():
                        logging.error(f"No se encontró un sensor para el índice {sensor_idx}. Saltando procesamiento.")
                        continue
                    sensor = sensors[sensor_idx]  # Obtener el sensor correspondiente
                    if sensor.is_critical():
                        logging.warning(f"Sensor {sensor.name} en estado crítico. Saltando procesamiento.")
                        continue
                        
                        try:
                            start_time = time.time()
                            process_sensor(
                                mux_manager,
                                sensor=sensors[sensor_idx],
                                channel=sensor_config['channel'],
                                sensor_name=sensor_config['sensor_name'],
                                thresholds=config['plastic_thresholds'],
                                data_queue=data_queue,
                                alert_manager=alert_manager,
                            )
                            processing_time = (time.time() - start_time) * 1000  # # Convertir a milisegundos
                            performance_tracker.add_reading(processing_time) # Agregar lectura al PerformanceTracker
                            logging.info(f"Tiempo de procesamiento: {processing_time:.2f} ms")
                        except Exception as e:
                            processing_time = 0
                            logging.error(f"Error procesando el sensor {sensor_config['sensor_name']}: {e}")
                            alert_manager.send_alert(
                                level="CRITICAL",
                                message=f"Error procesando el sensor {sensor_config['sensor_name']}",
                                metadata={"sensor": sensor_config['sensor_name'], "error": str(e)},
                            )
                        time.sleep(config['sensors']['read_interval'])
                    else:
                        logging.error(f"No se encontró un sensor para el indice {sensor_idx}.")
                    
                # Publicar métricas periódicamente
                if time.time() - last_metrics_publish_time > METRICS_INTERVAL:
                    average_time = performance_tracker.get_average_time()
                    if average_time:
                        metrics_payload = {
                            "average_processing_time_ms": average_time.total_seconds() * 1000,
                            "total_readings": performance_tracker.num_readings
                        }
                        mqtt_client.publish("raspberry-1/performance_metrics", json.dumps(metrics_payload))
                        logging.info(f"Métricas publicadas: {metrics_payload}")
                    last_metrics_publish_time = time.time()

                    # Ahorro de energía
                    run_power_saving_mode(mux_manager, sensors)
                    
    except Exception as e:
        error_message = f"Error en el loop principal: {e}"
        logging.critical(f"Error crítico: {e}")
        if alert_manager:
            alert_manager.send_alert(
                level="CRITICAL",
                message="Error en el loop principal",
                metadata={"error": str(e)}
            )
        
    except KeyboardInterrupt:
        logging.info("Programa detenido por el usuario.")
    except RuntimeError as e:
        logging.error(f"Error crítico en el sistema: {e}")
    except Exception as e:
        logging.critical(f"Error desconocido: {e}")
    finally:
        # Detener monitoreo de red
        if network_manager:
            network_manager.stop_monitoring()
            logging.info("Monitoreo de red detenido.")
        # Desconectar MQTT si está inicializado
        if mqtt_client and hasattr(mqtt_client, 'disconnect'):
            try:
                mqtt_client.disconnect()
                logging.info("Cliente MQTT desconectado.")
            except Exception as e:
                logging.error(f"Error al desconectar MQTT: {e}")
        else:
            logging.warning("El cliente MQTT no tiene un método de desconexión.")
            
        # Detener monitoreo de configuración en tiempo real
        config_manager.stop_monitoring()
        logging.info("Sistema apagado correctamente.")

if __name__ == "__main__":
    main()