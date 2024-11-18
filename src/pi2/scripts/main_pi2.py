import paho.mqtt.client as mqtt
import yaml
from utils import valve_control
import logging

# Cargar la configuración desde el archivo YAML
def load_config():
    print("Loading configuration for Raspberry Pi 2...")
    with open('config/pi2_config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    print("Configuration loaded.")
    return config

def on_message(client, userdata, message):
    """
    Función que maneja los mensajes recibidos a través de MQTT.
    """
    print(f"Message received on topic {message.topic}: {message.payload}")
    if message.topic == "plastics/pi2/valve1":
        print("Activating Valve 1 (PET detected).")
        valve_control.adjust_valves("valve1", {"value": 9})  # Simular activación de válvula 1
    elif message.topic == "plastics/pi2/valve2":
        print("Activating Valve 2 (HDPE detected).")
        valve_control.adjust_valves("valve2", {"value": 9})  # Simular activación de válvula 2

def main():
    # Cargar la configuración
    config = load_config()

    # Configurar logging
    logging.basicConfig(filename=config['logging']['log_file'], level=logging.INFO)
    print("Logging configured.")

    # Crear cliente MQTT y conectarse a AWS IoT Core
    client = mqtt.Client()

    # Configurar autenticación y TLS
    client.tls_set(ca_certs=config['aws']['ca_path'], 
                   certfile=config['aws']['cert_path'], 
                   keyfile=config['aws']['key_path'])

    # Conectar a AWS IoT Core
    client.connect(config['aws']['iot_core_endpoint'], port=8883)

    # Suscribirse a los tópicos para las válvulas
    client.subscribe("plastics/pi2/valve1")  # Tópico para la válvula 1 (PET)
    client.subscribe("plastics/pi2/valve2")  # Tópico para la válvula 2 (HDPE)

    # Asignar función para manejar mensajes recibidos
    client.on_message = on_message

    # Iniciar el loop de MQTT para esperar mensajes
    client.loop_forever()

if __name__ == '__main__':
    main()
