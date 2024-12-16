# main.py - Script principal para el control de relés y la comunicación MQTT    
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import json
import logging
from config_loader import load_config
from mqtt_client import create_mqtt_client, subscribe_to_topic, publish_message
from relay_controller import RelayController
from network_manager import NetworkManager

# Cargar configuración
config = load_config()

# Configuración de red
network_manager = NetworkManager(config)
network_manager.start_monitoring()

# Configuración del controlador de relés
relay_addresses = [0x18, 0x19]  # Direcciones I2C de los relés
relay_controller = RelayController(relay_addresses)

# Variables de configuración MQTT
broker_addresses = config['mqtt']['broker_addresses']
port = config['mqtt']['port']
client_id = config['mqtt']['client_id']
topic_action = config['mqtt']['topics']['action']
topic_status = config['mqtt']['topics']['status']

# Función para manejar el control de los relés según el tipo de material
def handle_relay_control(material_type, duration):
    if material_type == 'PET':
        relay_controller.activate_relay(0, duration)  # Activar relé 1
        logging.info(f"[MAIN] [RELAY] Activando Relay 1 (PET) por {duration} segundos")
    elif material_type == 'HDPE':
        relay_controller.activate_relay(1, duration)  # Activar relé 2
        logging.info(f"[MAIN] [RELAY] Activando Relay 2 (HDPE) por {duration} segundos")
    else:
        logging.info(f"[MAIN] [RELAY] Material desconocido: {material_type}")

# Callback para manejar mensajes MQTT
def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    if msg.topic == topic_action:
        material_type = payload.get('tipo')
        duration = payload.get('tiempo')
        if material_type and duration:
            handle_relay_control(material_type, duration)
            # Publicar estado del relé
            publish_message(client, topic_status, {'bucket_info': f'Bucket para {material_type}'})

# Crear cliente MQTT
mqtt_client = create_mqtt_client(client_id, broker_addresses, port, config['mqtt']['keepalive'], on_message)

# Suscribirse al tema de acción
subscribe_to_topic(mqtt_client, topic_action)

# Iniciar bucle MQTT
mqtt_client.loop_forever()
