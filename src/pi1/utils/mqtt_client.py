# mqtt_client.py - Utilidades para la conexión MQTT.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import paho.mqtt.client as mqtt
import logging

def create_mqtt_client(client_id, broker_addresses, port, keepalive):
    """
    Crea un cliente MQTT y lo conecta a uno de los brokers configurados.
    """
    #client = mqtt.Client(client_id="Raspberry_Pi-1", protocol=MQTTv311)
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)


    # Callback de conexión
    def on_connect(client, userdata, flags, rc):
        logging.info("[MQTT] Conectado exitosamente al broker MQTT.")
        if not rc == 0:
            logging.error(f"[MQTT] Error al conectar. Código: {rc}")

    client.on_connect = on_connect

    # Conexión a los brokers en orden
    for broker in broker_addresses:
        try:
            logging.info(f"[MQTT] Conectando al broker: {broker}")
            client.connect(broker, port, keepalive)
            return client
        except Exception as e:
            logging.error(f"[MQTT] Error al conectar con {broker}: {e}")

    raise Exception("[MQTT] No se pudo conectar a ningún broker MQTT.")

def subscribe_to_topic(client, topic):
    """
    Se suscribe a un tema MQTT.
    """
    client.subscribe(topic)
    logging.info(f"[MQTT] [CLIENT] Suscrito al tema: {topic}")