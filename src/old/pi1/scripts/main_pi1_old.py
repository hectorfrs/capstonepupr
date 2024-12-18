import yaml
from utils import sensors, iot_core, greengrass, networking
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

    # Configuración de red con redundancia
    print(f"Setting up redundant network configuration...")
    networking.setup_network(config['network'])

    # Configurar logging
    logging.basicConfig(filename=config['logging']['log_file'], level=logging.INFO)
    print("Logging configured.")

    # Leer datos de los sensores
    print(f"Reading sensor 1: {config['sensors']['sensor1']}")
    sensor_data1 = sensors.read_sensor(config['sensors']['sensor1'])
    print(f"Sensor 1 data: {sensor_data1}")
    
    print(f"Reading sensor 2: {config['sensors']['sensor2']}")
    sensor_data2 = sensors.read_sensor(config['sensors']['sensor2'])
    print(f"Sensor 2 data: {sensor_data2}")

    print(f"Reading sensor 3: {config['sensors']['sensor3']}")
    sensor_data3 = sensors.read_sensor(config['sensors']['sensor3'])
    print(f"Sensor 3 data: {sensor_data3}")

    # Consolidar los datos de los sensores
    sensor_data = {
        'sensor1': sensor_data1,
        'sensor2': sensor_data2,
        'sensor3': sensor_data3
    }

    # Enviar datos a AWS IoT Core utilizando MQTT con autenticación
    print(f"Sending data to AWS IoT Core on topic {config['aws']['iot_topic']}")
    iot_core.send_data_to_aws(config['aws']['iot_core_endpoint'], 
                              config['aws']['iot_topic'], 
                              sensor_data, 
                              config['aws']['cert_path'], 
                              config['aws']['key_path'], 
                              config['aws']['ca_path'])

    # Procesar los datos localmente con AWS IoT Greengrass
    print(f"Processing data with AWS IoT Greengrass group {config['aws']['greengrass_group']}")
    greengrass.process_with_greengrass(config['aws']['greengrass_group'], sensor_data)

    # Registrar la operación
    logging.info(f"Data sent to AWS IoT Core and Greengrass processed: {sensor_data}")

if __name__ == '__main__':
    main()
