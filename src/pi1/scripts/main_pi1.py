import yaml
from lib.as7265x import AS7265x  # Importar la librería para el sensor AS7265x
from lib.as7263_nir import AS7263NIR  # Importar la librería para el sensor AS7263 NIR
from utils import iot_core
import logging

# Cargar la configuración desde el archivo YAML
def load_config():
    print("Loading configuration for Raspberry Pi 1...")
    with open('config/pi1_config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    print("Configuration loaded.")
    return config

def main():
    # Cargar la configuración
    config = load_config()

    # Configurar logging
    logging.basicConfig(filename=config['logging']['log_file'], level=logging.INFO)
    print("Logging configured.")

    # Inicializar los sensores
    sensor_as7265x = AS7265x()  # Inicializar el sensor AS7265x
    sensor_as7263_nir = AS7263NIR()  # Inicializar el sensor AS7263 NIR

    # Leer datos de los sensores
    as7265x_data = sensor_as7265x.read_sensor_data()  # Leer datos del sensor AS7265x
    as7263_nir_data = sensor_as7263_nir.read_sensor_data()  # Leer datos del sensor AS7263 NIR

    # Simulación de la lógica de detección de tipo de plástico
    if as7265x_data['type'] == "PET":
        print("PET detected. Publishing message to activate Valve 1 on Raspberry Pi 2.")
        iot_core.send_data_to_aws(config['aws']['iot_core_endpoint'], 
                                  "plastics/pi2/valve1",   # Tópico para activar la válvula 1
                                  {"action": "activate_valve_1"}, 
                                  config['aws']['cert_path'], 
                                  config['aws']['key_path'], 
                                  config['aws']['ca_path'])
    elif as7265x_data['type'] == "HDPE":
        print("HDPE detected. Publishing message to activate Valve 2 on Raspberry Pi 2.")
        iot_core.send_data_to_aws(config['aws']['iot_core_endpoint'], 
                                  "plastics/pi2/valve2",   # Tópico para activar la válvula 2
                                  {"action": "activate_valve_2"}, 
                                  config['aws']['cert_path'], 
                                  config['aws']['key_path'], 
                                  config['aws']['ca_path'])

    # Registrar la operación
    logging.info(f"Plastic detected: {as7265x_data['type']}. Message published to Raspberry Pi 2.")

if __name__ == '__main__':
    main()
