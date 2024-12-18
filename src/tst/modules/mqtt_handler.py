# mqtt_handler.py - Clase centralizada para manejar conexiones MQTT y la publicación de mensajes.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import paho.mqtt.client as mqtt
import uuid
import boto3
from modules.logging_manager import LoggingManager
from modules.config_manager import ConfigManager

class MQTTHandler:
    """
    Clase centralizada para manejar conexiones MQTT y la publicación de mensajes.
    Soporta funcionalidades locales y opcionales para AWS IoT.
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Inicializa la clase MQTTHandler con la configuración proporcionada.

        :param config_manager: Instancia de ConfigManager para manejar configuraciones centralizadas.
        """
        self.config_manager = config_manager
        self.config = self.config_manager.get("mqtt", {})
        self.enable_mqtt = self.config_manager.get("mqtt.enable_mqtt", True)
        self.enable_aws = self.config_manager.get("mqtt.enable_aws", False)

        # Configurar logger centralizado
        self.logger = setup_logger("[MQTT_HANDLER]", self.config_manager.get("logging", {}))

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

    def disconnect(self):
        """
        Desconecta del broker MQTT.
        """
        if not self.enable_mqtt:
            self.logger.warning("MQTT está deshabilitado. Desconexión omitida.")
            return

        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.info("[MQTT] Desconectado del broker exitosamente.")
        except Exception as e:
            self.logger.error(f"[MQTT] Error al desconectar del broker: {e}")

    def is_connected(self):
        """
        Verifica si el cliente MQTT está conectado al broker.

        :return: True si está conectado, False en caso contrario.
        """
        if not self.enable_mqtt:
            self.logger.warning("MQTT está deshabilitado. Estado de conexión omitido.")
            return False

        try:
            return self.client.is_connected()
        except Exception as e:
            self.logger.error(f"[MQTT] Error verificando conexión al broker: {e}")
            return False

    def forever_loop(self):
        """
        Ejecuta el loop MQTT para mantener la conexión y procesar mensajes de forma continua.
        """
        if not self.enable_mqtt:
            self.logger.warning("MQTT está deshabilitado. Loop omitido.")
            return

        try:
            self.logger.info("[MQTT] Iniciando loop continuo...")
            self.client.loop_forever()
        except Exception as e:
            self.logger.error(f"[MQTT] Error en loop continuo: {e}")

    def reconnect(self):
        """
        Reintenta la conexión automáticamente en caso de desconexión si `auto_reconnect` está habilitado.
        """
        if not self.enable_mqtt or not self.auto_reconnect:
            self.logger.warning("Reconexión automática está deshabilitada.")
            return

        try:
            while not self.is_connected():
                self.logger.info("[MQTT] Intentando reconectar al broker...")
                self.connect()
                time.sleep(5)
        except Exception as e:
            self.logger.error(f"[MQTT] Error durante la reconexión automática: {e}")

    def publish(self, topic, message, qos=0):
        """
        Publica un mensaje en un tópico MQTT, agregando un ID único para trazabilidad.

        :param topic: Tópico al que se publicará el mensaje.
        :param message: Mensaje a publicar (en formato JSON).
        :param qos: Nivel de calidad del servicio (QoS) para el mensaje.
        """
        if not self.enable_mqtt:
            self.logger.warning("MQTT está deshabilitado. Publicación omitida.")
            return

        try:
            # Agregar ID único al mensaje
            message_with_id = message.copy() if isinstance(message, dict) else {"message": message}
            message_with_id["id"] = str(uuid.uuid4())

            result = self.client.publish(topic, str(message_with_id), qos=qos)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"[MQTT] Mensaje publicado en {topic}: {message_with_id}")
            else:
                self.logger.error(f"[MQTT] Error al publicar mensaje en {topic}: Código {result.rc}")
        except Exception as e:
            self.logger.error(f"[MQTT] Error publicando mensaje en {topic}: {e}")
