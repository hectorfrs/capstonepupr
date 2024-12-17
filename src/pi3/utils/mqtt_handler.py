# mqtt_handler.py - Módulo para manejo de cliente MQTT
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import logging
import json
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

class MQTTHandler:
    def __init__(self, client_id, broker_address, port, keepalive, topics=None):
        """
        Inicializa el cliente MQTT con las configuraciones especificadas.
        :param client_id: ID único del cliente MQTT.
        :param broker_address: Dirección del broker MQTT.
        :param port: Puerto del broker MQTT.
        :param keepalive: Tiempo máximo para mantener la conexión activa.
        :param topics: Lista de tópicos para suscribirse.
        """
        self.logger = logging.getLogger("MQTTHandler")
        self.client_id = client_id
        self.broker_address = broker_address
        self.port = port
        self.keepalive = keepalive
        self.topics = topics if topics else []
        self.client = mqtt.Client(client_id)
        self._configure_callbacks()

    def _configure_callbacks(self):
        """Configura los callbacks para el cliente MQTT."""
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc):
        """Callback al conectar al broker."""
        if rc == 0:
            logging.info("[MQTT] Conexión exitosa al broker MQTT.")
            for topic in self.topics:
                client.subscribe(topic)
                logging.info(f"[MQTT] Suscrito al tópico: {topic}")
        else:
            logging.error(f"[MQTT] Fallo al conectar. Código de retorno: {rc}")

    def on_message(self, client, userdata, msg):
        """Callback al recibir un mensaje."""
        payload = msg.payload.decode()
        logging.info(f"[MQTT] Mensaje recibido en {msg.topic}: {payload}")

    def on_disconnect(self, client, userdata, rc):
        """Callback al desconectar del broker."""
        logging.warning(f"[MQTT] Cliente desconectado del broker.")
        logging.warning(f"[MQTT] Código de retorno: {rc}")
        while rc != 0:
            try:
                logging.info("[MQTT] Intentando reconectar...")
                rc = client.reconnect()
            except Exception as e:
                logging.error(f"[MQTT] Error al reconectar: {e}")
                time.sleep(5)


    def connect(self):
        """Conecta el cliente MQTT al broker."""
        try:
            self.client.connect(self.broker_address, self.port, self.keepalive)
            logging.info(f"[MQTT] Conectado al broker: {self.broker_address}:{self.port}")
        except Exception as e:
            logging.error(f"[MQTT] Error al conectar al broker: {e}")
            raise e

    def publish(self, topic, payload):
        """
        Publica un mensaje en un tópico.
        :param topic: Tópico donde se enviará el mensaje.
        :param payload: Carga útil del mensaje en formato JSON.
        """
        try:
            message = json.dumps(payload)
            self.client.publish(topic, message)
            logging.info(f"[MQTT] Mensaje publicado en {topic}: {message}")
        except Exception as e:
            logging.error(f"[MQTT] Error al publicar mensaje en {topic}: {e}")

    def loop_forever(self):
        """Inicia el bucle principal de MQTT para manejar la comunicación."""
        try:
            logging.info("[MQTT] Iniciando bucle MQTT...")
            self.client.loop_forever()
        except KeyboardInterrupt:
            logging.info("[MQTT] Interrumpido manualmente. Finalizando bucle.")
            self.client.disconnect()

    def subscribe(self, topic):
        """
        Se suscribe a un tópico adicional.
        :param topic: Tópico a suscribirse.
        """
        self.client.subscribe(topic)
        logging.info(f"[MQTT] Suscrito manualmente al tópico: {topic}")
