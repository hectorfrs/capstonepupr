# main.py - Script principal para la captura de datos de los sensores AS7265x
# Desarrollado por Héctor F. Rivera Santiago
# copyright (c) 2024

import logging
import yaml
import qwiic
import time
import sys
import os
from lib.TCA9548A_HighLevel import TCA9548AMUXHighLevel
from lib.AS7265x_HighLevel import AS7265xSensorHighLevel
from lib.AS7265x_HighLevel import generate_summary

# Agregar la ruta del proyecto al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Cargar configuración desde el archivo config.yaml
config_path = "/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config_optimized.yaml"
def load_config(file_path=config_path):
    try:
        with open(file_path, "r") as file:
            config = yaml.safe_load(file)
            logging.info("[CONFIG] Archivo de configuración cargado correctamente.")
            return config
    except Exception as e:
        logging.error(f"[CONFIG] Error al cargar el archivo de configuración: {e}")
        raise

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
    config = load_config()

    # Configuración de logging
    configure_logging(config)
    logging.info("[MAIN] Sistema iniciado en Raspberry Pi #1...")

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
    logging.info("[MUX] Inicializando...")
    mux = TCA9548AMUXHighLevel(address=config['mux']['address'])

    # Habilitar canales del MUX
    mux_channels = [entry['channel'] for entry in config['mux']['channels']]
    mux.enable_multiple_channels(mux_channels)

    # Inicializar sensores en los canales
    logging.info("[SENSOR] Inicializando...")
    sensors = []
    for channel_entry in config["mux"]["channels"]:
        channel = channel_entry["channel"]
        sensor_name = channel_entry["sensor_name"]

        logging.info(f"[SENSOR] Inicializando sensor en canal {channel}...")
        mux.enable_channel(channel)
        logging.info(
            f"[MUX] El canal {channel} ha sido habilitado. "
            f"Esperando estabilización del sensor..."
            )
        time.sleep(0.5)    # Tiempo de estabilización a 500 ms
        
        try:
            # Crea instancia High Level para el sensor
            sensor = AS7265xSensorHighLevel()
            # Reset y Verificar el estado del sensor
            sensor.reset()
            time.sleep(5)  # Esperar 5 segundo después de resetear
            status = sensor.read_status()
            logging.debug(f"[SENSOR] Estado del sensor después del reinicio: {bin(status)}")

            # Configurar el sensor
            logging.info("[SENSOR] El sensor está listo para ser configurado.")
            sensor.configure()
            sensors.append(sensor)
            if not sensors:
                logging.error(f"[SENSOR] No se inicializaron sensores correctamente. Finalizando el programa.")
                return
            logging.info(
                f"[CANAL {channel} Sensor configurado: {sensor_name}] "
                f"Integración={integration_time}ms, Ganancia={gain}x, Modo={mode}."
                )

            # Deshabilitar todos los canales después de configurar el sensor
            mux.disable_all_channels()
        except Exception as e:
            logging.error(f"[SENSOR] Error con el sensor en canal {channel}: {e}")
            continue
        finally:
            # Deshabilitar todos los canales después de configurar el sensor
            mux.disable_all_channels()

    # Capturar datos de los sensores
    start_time = time.time()
    for idx, sensor in enumerate(sensors):
        try:
            # Habilitar el canal correspondiente
            mux.enable_channel(mux_channels[idx])
            logging.info(f"[CANAL {mux_channels[idx]}] Habilitado para lectura.")
            time.sleep(1.0)

            # Determinar el tipo de lectura según la configuración
            read_calibrated = config["system"].get("read_calibrated_data", True)

            # Realizar la lectura
            if read_calibrated:
                logging.info(f"[SENSOR] Realizando lectura calibrada del sensor {idx} en canal {mux_channels[idx]}")
                spectrum = sensor.read_calibrated_spectrum()
                successful_reads += 1
            else:
                logging.info(f"[SENSOR] Realizando lectura datos crudos del sensor {idx} en canal {mux_channels[idx]}")
                spectrum = sensor.read_raw_spectrum()

            #logging.info(f"Datos leidos de sensor {idx} en canal {mux_channels[idx]}: {spectrum}")

        except Exception as e:
            failed_reads += 1
            error_details.append({"channel": {mux_channels[idx]}, "error_message": str(e)})
            logging.error(
                f"[SENSOR] Error en función 'read_calibrated_spectrum' al procesar el sensor {idx} en canal {mux_channels[idx]}: {e}"
                f"Verifique la conexion I2C y los parametros de configuración.")
        except Exception as main_error:
            print (f"Error general en el programa: {main_error}")
        finally:
            mux.disable_all_channels()
            elapsed_time = time.time() - start_time
            logging.info(
                f"[SENSOR] Captura completada.\n"
                f"[MUX] Todos los canales deshabilitados.\n"
                f"Tiempos de ejecución: {elapsed_time:.2f} segundos.\n"
                )
    generate_summary(successful_reads, failed_reads, error_details)
    # Deshabilitar todos los canales del MUX al finalizar
    #logging.debug(f"Sensores inicializados: {sensors}")
    #logging.debug(f"Canales del MUX: {mux_channels}")

    

if __name__ == "__main__":
    main()
