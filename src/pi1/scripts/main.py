# main.py - Script principal para la captura de datos de los sensores AS7265x
# Desarrollado por Héctor F. Rivera Santiago
# copyright (c) 2024

import logging
import yaml
import qwiic
from classes.TCA9548A_Manager import TCA9548AManager
from classes.AS7265x_Manager import AS7265xManager



# Configuración de logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Cargar configuración desde el archivo config.yaml
config_path = "/home/raspberry-1/capstonepupr/src/pi1/config/pi1_config_optimized.yaml"
def load_config(file_path=config_path):
    try:
        with open(file_path, "r") as file:
            config = yaml.safe_load(file)
            logging.info("Archivo de configuración cargado correctamente.")
            return config
    except Exception as e:
        logging.error(f"Error al cargar el archivo de configuración: {e}")
        raise

def scan_i2c_bus():
    """
    Escanea el bus I2C y devuelve una lista de dispositivos detectados.
    """
    devices = qwiic.scan()
    if devices:
        logging.info(f"Dispositivos detectados en el bus I2C: {[hex(addr) for addr in devices]}")
    else:
        logging.warning("No se detectaron dispositivos en el bus I2C.")
    return devices

# Función principal
def main():
    # Cargar configuración
    config = load_config()

    # Escanear el bus I2C
    detected_devices = scan_i2c_bus()

    # Verificar si las direcciones esperadas están presentes
    expected_devices = [0x70, 0x49]  # Dirección del MUX y del sensor AS7265x
    for device in expected_devices:
        if device not in detected_devices:
            logging.error(f"Dispositivo con dirección {hex(device)} no encontrado.")
        else:
            logging.info(f"Dispositivo con dirección {hex(device)} detectado correctamente.")
    
    # Inicializar MUX
    logging.info("Inicializando MUX...")
    mux_address = hex(config["mux"]["address"])
    mux = TCA9548AManager(int(mux_address, 16))

    # Habilitar canales del MUX
    logging.info (f"Inicializando canales del MUX: {mux_address}")
    mux_channels = config["mux"]["channels"]
    mux_channels = [entry['channel'] for entry in config['mux']['channels']]
    mux.enable_multiple_channels(mux_channels)

    # Inicializar sensores en los canales
    logging.info("Inicializando sensores en los canales del MUX...")
    sensors = []
    for channel in mux_channels:
        logging.info(f"Inicializando sensor en canal {channel}...")
        mux.enable_channel(channel)
        sensor = AS7265xManager()
        sensor.configure(
            integration_time=config["sensors"]["integration_time"],
            gain=config["sensors"]["gain"],
            mode=config["sensors"]["mode"]
        )
        sensors.append(sensor)
        logging.info(f"Sensor en canal {channel} configurado correctamente.")

    # Capturar datos de los sensores
    for idx, sensor in enumerate(sensors):
        logging.info(f"Capturando datos del sensor {idx} en canal {mux_channels[idx]}")
        spectrum = sensor.read_calibrated_spectrum()
        logging.info(f"Espectro calibrado del sensor {idx}: {spectrum}")

    # Deshabilitar todos los canales del MUX al finalizar
    mux.disable_all_channels()
    logging.info("Pruebas completadas. Todos los canales deshabilitados.")

if __name__ == "__main__":
    main()
