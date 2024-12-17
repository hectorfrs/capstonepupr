# mqtt_client.py - Utilidades para la conexión y publicación de mensajes MQTT.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

from paho.mqtt.client import Client, MQTTv311
import json
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s' , datefmt='%Y-%m-%d %H:%M:%S')

def create_mqtt_client(client_id, broker_addresses, port, keepalive, on_message=None):
    """
    Crea un cliente MQTT y lo conecta al primer broker disponible.
    """
    # Forzar el uso de MQTT 3.1.1 para mayor compatibilidad
    #client = Client(client_id, protocol=MQTTv311)
    client = Client(client_id=client_id, protocol=MQTTv311) 


    # Configurar callback para mensajes
    if on_message:
        client.on_message = on_message

    # Intentar conectarse a cada broker proporcionado
    for broker in broker_addresses:
        try:
            client.connect(broker, port, keepalive)
            logging.info(f"[MQTT] [CLIENT] Conectado al broker MQTT: {broker}")
            return client
        except Exception as e:
            logging.error(f"[MQTT] [CLIENT] Error al conectar con el broker {broker}: {e}")

    # Si no se puede conectar a ningún broker, lanza una excepción
    raise Exception("[MQTT] [CLIENT] No se pudo conectar a ningún broker MQTT.")

def publish_message(client, topic, payload):
    """
    Publica un mensaje en un tema MQTT.
    """
    client.publish(topic, json.dumps(payload))
    logging.info(f"[MQTT] [CLIENT] Publicado en {topic}: {payload}")

def subscribe_to_topic(client, topic):
    """
    Se suscribe a un tema MQTT.
    """
    client.subscribe(topic)
    logging.info(f"[MQTT] [CLIENT] Suscrito al tema: {topic}")

def on_disconnect(self, client, userdata, rc):
    logging.warning(f"[MQTT] Desconectado. Código de retorno: {rc}")
    while rc != 0:
        try:
            logging.info("[MQTT] Intentando reconectar...")
            rc = client.reconnect()
        except Exception as e:
            logging.error(f"[MQTT] Error al reconectar: {e}")
            time.sleep(5)
    logging.info("[MQTT] Reconectado exitosamente.")
