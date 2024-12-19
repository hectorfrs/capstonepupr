# mqtt_handler.py - Clase centralizada para manejar conexiones MQTT y la publicación de mensajes.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import paho.mqtt.client as mqtt
import uuid
import boto3
import time
from modules.logging_manager import LoggingManager
from modules.config_manager import ConfigManager

class MQTTHandler:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = self.config_manager.get("mqtt", {})
        self.enable_mqtt = self.config.get("enable_mqtt", True)
        self.auto_reconnect = self.config.get("auto_reconnect", True)
        self.broker_addresses = self.config.get("broker_addresses", [])
        self.topics = self.config.get("topics", {})
        self.client_id = self.config.get("client_id", "DefaultClient")
        self.port = self.config.get("port", 1883)
        self.keepalive = self.config.get("keepalive", 60)

        # Validar y normalizar broker_addresses
        if isinstance(self.broker_addresses, str):
            self.broker_addresses = [self.broker_addresses]
        if not all(isinstance(broker, str) for broker in self.broker_addresses):
            raise ValueError("[MQTT] broker_addresses debe contener solo strings.")

        # Inicializar cliente MQTT
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        # Configurar logger
        logging_manager = LoggingManager(self.config_manager)
        self.logger = logging_manager.setup_logger("[MQTT_HANDLER]")

        self.logger.info(f"[MQTT] Brokers configurados: {self.broker_addresses}")
        self.logger.info(f"[MQTT] Tópicos configurados: {self.topics}")

    def connect(self):
        """
        Intenta conectar al primer broker disponible.
        """
        for broker in self.broker_addresses:
            try:
                self.logger.info(f"[MQTT] Intentando conectar al broker {broker}:{self.port}...")
                self.client.connect(broker, self.port, self.keepalive)
                self.client.loop_start()
                self.subscribe_to_topics()
                self.logger.info(f"[MQTT] Conexión exitosa al broker {broker}:{self.port}.")
                return
            except Exception as e:
                self.logger.warning(f"[MQTT] No se pudo conectar al broker {broker}:{self.port}. Error: {e}")

        self.logger.critical("[MQTT] No se pudo conectar a ninguno de los brokers disponibles.")
        raise ConnectionError("[MQTT] No se pudo conectar a ningún broker MQTT.")

    def subscribe_to_topics(self):
        """
        Suscribe al cliente MQTT a los tópicos configurados.
        """
        if not self.topics:
            self.logger.warning("[MQTT] No se encontraron tópicos para suscripción.")
            return

        for topic_name, topic_path in self.topics.items():
            try:
                self.client.subscribe(topic_path)
                self.logger.info(f"[MQTT] Suscrito al tópico: {topic_path}")
            except Exception as e:
                self.logger.error(f"[MQTT] Error al suscribirse al tópico {topic_path}: {e}")

    def unsubscribe(self, topics):
        """
        Se desuscribe de uno o varios tópicos.
        """
        for topic in topics:
            try:
                self.client.unsubscribe(topic)
                self.logger.info(f"[MQTT] Desuscrito del tópico: {topic}")
            except Exception as e:
                self.logger.error(f"[MQTT] Error al desuscribirse del tópico {topic}: {e}")

    def publish(self, topic, message, qos=0):
        """
        Publica un mensaje en un tópico MQTT.
        """
        try:
            self.client.publish(topic, message, qos=qos)
            self.logger.info(f"[MQTT] Mensaje publicado en {topic}: {message}")
        except Exception as e:
            self.logger.error(f"[MQTT] Error al publicar mensaje en {topic}: {e}")

    def is_connected(self):
        """
        Verifica si el cliente MQTT está conectado.
        """
        return self.client.is_connected()

    def reconnect(self):
        """
        Intenta reconectar al broker MQTT.
        """
        try:
            self.logger.info("[MQTT] Intentando reconexión...")
            self.client.reconnect()
        except Exception as e:
            self.logger.error(f"[MQTT] Error al intentar reconexión: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("[MQTT] Conexión exitosa al broker MQTT.")
        else:
            self.logger.error(f"[MQTT] Error al conectar al broker MQTT. Código: {rc}")

    def on_disconnect(self, client, userdata, rc):
        self.logger.warning("[MQTT] Desconectado del broker MQTT.")
        if self.auto_reconnect:
            self.logger.info("[MQTT] Intentando reconexión automática...")
            self.reconnect()

    def on_message(self, client, userdata, msg):
        self.logger.info(f"[MQTT] Mensaje recibido en {msg.topic}: {msg.payload.decode()}")

    def loop_forever(self):
        """
        Mantiene activo el bucle de recepción de mensajes.
        """
        try:
            self.logger.info("[MQTT] Iniciando loop continuo...")
            self.client.loop_forever()
        except Exception as e:
            self.logger.error(f"[MQTT] Error en loop continuo: {e}")
