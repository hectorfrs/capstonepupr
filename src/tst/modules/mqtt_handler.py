# mqtt_handler.py - Clase centralizada para manejar conexiones MQTT y la publicación de mensajes.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import uuid
import boto3

class MQTTHandler:
    """
    Clase centralizada para manejar conexiones MQTT y la publicación de mensajes.
    Soporta funcionalidades locales y opcionales para AWS IoT.
    """

    def __init__(self, config_manager):
        """
        Inicializa la clase MQTTHandler con la configuración proporcionada.

        :param config_manager: Instancia de ConfigManager para manejar configuraciones centralizadas.
        """
        from modules.logging_manager import LoggingManager
        import paho.mqtt.client as mqtt

        self.config_manager = config_manager
        self.config = self.config_manager.get("mqtt", {})
        self.enable_mqtt = self.config_manager.get("mqtt.enable_mqtt", True)
        self.enable_aws = self.config_manager.get("mqtt.enable_aws", False)

        # Configurar logger centralizado
        self.logger = LoggingManager(config_manager).setup_logger("[MQTT_HANDLER]")

        # Configuración local MQTT
        if self.enable_mqtt:
            self.broker = self.config.get("broker_addresses", ["localhost"])[0]
            self.port = self.config.get("port", 1883)
            self.keepalive = self.config.get("keepalive", 60)
            self.client_id = self.config.get("client_id", "MQTTClient")

            # Inicializar cliente MQTT
            self.client = mqtt.Client(client_id=self.client_id)

            # Configuración de callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish
            self.client.on_message = self.on_message

        # Configuración AWS IoT
        if self.enable_aws:
            aws_region = self.config_manager.get("aws.region", "us-east-1")
            self.aws_client = boto3.client('iot-data', region_name=aws_region)

        # Atributo para reconexión automática
        self.auto_reconnect = self.config_manager.get("mqtt.auto_reconnect", True)

    def connect(self):
        """
        Intenta conectarse a cada dirección de broker hasta que tenga éxito.
        """
        if not self.enable_mqtt:
            self.logger.warning("MQTT está deshabilitado. Conexión omitida.")
            return

        for broker in self.config.get("broker_addresses", []):
            try:
                self.logger.info(f"[MQTT] Intentando conectar al broker {broker}:{self.port}...")
                self.client.connect(broker, self.port, self.keepalive)
                self.client.loop_start()  # Inicia el loop de la biblioteca MQTT
                self.logger.info(f"[MQTT] Conexión exitosa al broker {broker}:{self.port}.")
                return  # Sale del método si la conexión tiene éxito
            except Exception as e:
                self.logger.warning(f"[MQTT] No se pudo conectar al broker {broker}:{self.port}. Error: {e}")

        # Si ninguna conexión tuvo éxito
        self.logger.critical("[MQTT] No se pudo conectar a ninguno de los brokers disponibles.")
        raise ConnectionError("No se pudo conectar a ningún broker MQTT.")
