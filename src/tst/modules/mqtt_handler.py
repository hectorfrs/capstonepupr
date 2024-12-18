# mqtt_handler.py - Clase centralizada para manejar conexiones MQTT y la publicación de mensajes.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import paho.mqtt.client as mqtt
import uuid
import boto3
import time
import json
import os
import sys
import logging
from modules.logging_manager import LoggingManager
from modules.config_manager import ConfigManager
class MQTTHandler:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = self.config_manager.get("mqtt", {})
        self.broker_addresses = self._normalize_brokers()
        self.client_id = self.config.get("client_id", "DefaultClient")
        self.port = self.config.get("port", 1883)
        self.keepalive = self.config.get("keepalive", 60)
        self.topics = self.config.get("topics", {})
        self.auto_reconnect = self.config.get("auto_reconnect", True)  
        self.logger = LoggingManager(self.config_manager).setup_logger("[MQTT_HANDLER]")

        if not self.broker_addresses:
            self.logger.critical("[MQTT] No se configuraron brokers en el archivo de configuración.")
            raise ValueError("No se configuraron brokers en el archivo de configuración.")

        # Inicializa el cliente MQTT
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        self.logger.info(f"Brokers configurados: {self.broker_addresses}")
        self.logger.info(f"Tópicos configurados: {self.topics}")
        
        
    def _normalize_brokers(self):
        """
        Valida y normaliza los brokers configurados.
        """
        mqtt_config = self.config.get("mqtt", {})
        if not mqtt_config:
            raise ValueError("[MQTT] La configuración MQTT no está definida en config.yaml.")

        broker_addresses = mqtt_config.get("broker_addresses")
        if not broker_addresses:
            raise ValueError(f"[MQTT] broker_addresses no configurados en mqtt. Archivo de configuración: {self.config_manager.config_path}")

        if isinstance(broker_addresses, str):
            logger.warning("[MQTT] broker_addresses era un string. Se convirtió a una lista.")
            broker_addresses = [broker_addresses]

        if not isinstance(broker_addresses, list):
            raise ValueError(f"[MQTT] broker_addresses debe ser una lista. Tipo encontrado: {type(broker_addresses)} en {self.config_manager.config_path}")

        self.brokers = broker_addresses
        logger.info(f"[MQTT] Brokers configurados: {self.brokers}")


    def connect_and_subscribe(self):
        """
        Conecta al primer broker disponible y suscribe a los tópicos configurados.
        """
        for broker in self.broker_addresses:
            try:
                self.logger.info(f"Intentando conectar al broker {broker}:{self.port}...")
                self.client.connect(broker, self.port, self.keepalive)
                self.client.loop_start()
                self._subscribe_to_topics()
                self.logger.info(f"Conexión exitosa al broker {broker}.")
                return
            except Exception as e:
                self.logger.warning(f"No se pudo conectar al broker {broker}:{self.port}. Error: {e}")

        self.logger.critical("No se pudo conectar a ninguno de los brokers disponibles.")
        raise ConnectionError("No se pudo conectar a ningún broker MQTT.")

    def _subscribe_to_topics(self):
        """
        Suscribe al cliente MQTT a los tópicos configurados.
        """
        if not self.topics:
            self.logger.warning("No hay tópicos configurados para suscripción.")
            return

        for topic_name, topic_path in self.topics.items():
            try:
                self.client.subscribe(topic_path)
                self.logger.info(f"Suscrito al tópico: {topic_path}")
            except Exception as e:
                self.logger.error(f"Error al suscribirse al tópico {topic_path}: {e}")

    def publish(self, topic, message, qos=0):
        """
        Publica un mensaje en un tópico MQTT con un ID único para rastreo.
        """
        try:
            # Agregar un ID único al mensaje
            if isinstance(message, dict):
                message["id"] = str(uuid.uuid4())
            else:
                message = {"message": message, "id": str(uuid.uuid4())}

            # Publicar el mensaje
            if not isinstance(message, str):
                message = json.dumps(message)  # Convertir a JSON válido
            self.client.publish(topic, message, qos=qos)
            self.logger.info(f"[MQTT] Mensaje publicado en {topic}: {message}")
        except Exception as e:
            self.logger.error(f"[MQTT] Error al publicar mensaje en {topic}: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("Conexión exitosa al broker MQTT.")
        else:
            self.logger.error(f"Fallo al conectar al broker. Código: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """
        Maneja desconexiones del broker MQTT.
        """
        self.logger.warning("[MQTT] Desconectado del broker MQTT.")
        if self.auto_reconnect:
            try:
                self.logger.info("[MQTT] Intentando reconexión automática...")
                self.connect_and_subscribe()
            except Exception as e:
                self.logger.error(f"[MQTT] Error en reconexión automática: {e}")

    def on_message(self, client, userdata, msg):
        """
        Maneja mensajes recibidos en los tópicos suscritos.
        """
        try:
            payload = msg.payload.decode()
            message = json.loads(payload)  # Usar json.loads en lugar de eval

            # Extraer ID único
            message_id = message.get("id", "Sin ID")
            self.logger.info(f"[MQTT] Mensaje recibido en {msg.topic}: {message}. ID: {message_id}")

            # Invocar callback personalizado
            if userdata and hasattr(userdata, "on_message_received"):
                userdata.on_message_received(message_id, msg.topic, message)
        except json.JSONDecodeError as e:
            self.logger.error(f"[MQTT] Error decodificando JSON: {e}")
        except Exception as e:
            self.logger.error(f"[MQTT] Error procesando mensaje en {msg.topic}: {e}")

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

