import logging
import time
from lib.AS7265x_HighLevel import AS7265xHighLevel
from lib.TCSA9548A_HighLevel import TCA9548AManager
from utils import load_config

def setup_logging(logging_config):
    """
    Configura el sistema de logging según el archivo de configuración.
    """
    logging.basicConfig(
        level=getattr(logging, logging_config['level']),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logging_config['file']),
            logging.StreamHandler()
        ]
    )

def process_individual_reading(config, sensor_high_level, mux):
    """
    Realiza el proceso actual de lectura de sensores, una vez.
    """
    logging.info("Iniciando proceso de lectura individual...")
    for channel_config in config['mux']['channels']:
        channel = channel_config['channel']
        sensor_name = channel_config['sensor_name']
        logging.info(f"Habilitando canal {channel} para {sensor_name}...")
        
        mux.enable_channel(channel)
        raw_data = sensor_high_level.read_raw_spectrum()
        logging.info(f"Datos leídos de {sensor_name}: {raw_data}")

        plastic, distance = identify_plastic_type(raw_data, config['plastic_spectra'])
        logging.info(f"{sensor_name} Identificado: {plastic} (Distancia: {distance:.2f})")
        
        mux.disable_channel(channel)
        logging.info(f"Canal {channel} deshabilitado.")
    logging.info("Proceso de lectura individual completado.")

def process_conveyor(config, sensor_high_level, mux):
    """
    Procesa lecturas del conveyor continuamente.
    """
    logging.info("Iniciando procesamiento continuo del conveyor...")
    try:
        while True:
            for channel_config in config['mux']['channels']:
                channel = channel_config['channel']
                sensor_name = channel_config['sensor_name']
                logging.info(f"Habilitando canal {channel} para {sensor_name}...")
                
                mux.enable_channel(channel)
                raw_data = sensor_high_level.read_raw_spectrum()
                logging.info(f"Datos leídos de {sensor_name}: {raw_data}")

                plastic, distance = identify_plastic_type(raw_data, config['plastic_spectra'])
                logging.info(f"{sensor_name} Identificado: {plastic} (Distancia: {distance:.2f})")
                
                mux.disable_channel(channel)
                logging.info(f"Canal {channel} deshabilitado.")
            time.sleep(1.0)  # Intervalo entre lecturas
    except KeyboardInterrupt:
        logging.info("Procesamiento continuo detenido por el usuario.")
    finally:
        mux.disable_all_channels()
        logging.info("Todos los canales deshabilitados.")

if __name__ == "__main__":
    # Cargar configuración
    config = load_config("config.yaml")

    # Configurar logging
    setup_logging(config['logging'])

    # Inicializar MUX
    mux = MUXController(address=config['mux']['address'])

    # Inicializar sensores
    sensor_high_level = AS7265xHighLevel()
    sensor_high_level.set_gain(config['sensors']['gain'])
    sensor_high_level.set_integration_time(config['sensors']['integration_time'])
    sensor_high_level.set_mode(config['sensors']['mode'])

    # Ejecutar proceso según configuración
    if config.get('process_with_conveyor', False):
        process_conveyor(config, sensor_high_level, mux)
    else:
        process_individual_reading(config, sensor_high_level, mux)
