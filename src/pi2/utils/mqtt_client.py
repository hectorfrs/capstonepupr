

from paho.mqtt.client import Client
import json
import logging

def create_mqtt_client(client_id, broker_addresses, port, keepalive, on_message=None):
    client = Client(client_id)
    if on_message:
        client.on_message = on_message
    for broker in broker_addresses:
        try:
            client.connect(broker, port, keepalive)
            logging.info(f"[MQTT] [CLIENT] Conectado al broker MQTT: {broker}")
            return client
        except Exception as e:
            logging.error(f"[MQTT] [CLIENT] Error al conectar con el broker {broker}: {e}")
    raise Exception("[MQTT] [CLIENT] No se pudo conectar a ningún broker MQTT.")

def publish_message(client, topic, payload):
    client.publish(topic, json.dumps(payload))
    logging.info(f"[MQTT] [CLIENT] Publicado en {topic}: {payload}")

def subscribe_to_topic(client, topic):
    client.subscribe(topic)
    logging.info(f"[MQTT] [CLIENT] Suscrito al tema: {topic}")
