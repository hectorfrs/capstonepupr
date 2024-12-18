# mqtt_handler.py - Clase centralizada para manejar conexiones MQTT y la publicación de mensajes.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import paho.mqtt.client as mqtt
import uuid
from modules.logging_manager import setup_logger

class MQTTHandler:
    """
    Clase centralizada para manejar conexiones MQTT y la publicación de mensajes.
    """

    def __init__(self, config, enable_mqtt=True):
        """
        Inicializa la clase MQTTHandler con la configuración proporcionada.

        :param config: Configuración para el cliente MQTT.
        :param enable_mqtt: Habilita o deshabilita la funcionalidad MQTT.
        """
        self.config = config
        self.enable_mqtt = enable_mqtt

        # Configurar logger centralizado
        self.logger = setup_logger("[MQTT_HANDLER]", config.get("logging", {}))

        if self.enable_mqtt:
            self.broker = config["broker_addresses"][0]  # Utilizar el primer broker como predeterminado
            self.port = config.get("port", 1883)
            self.keepalive = config.get("keepalive", 60)
            self.client_id = config.get("client_id", "MQTTClient")

            # Inicializar cliente MQTT
            self.client = mqtt.Client(client_id=self.client_id)

            # Configuración de callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish

    def connect(self):
        """
        Intenta conectarse a cada dirección de broker hasta que tenga éxito.
        """
        if not self.enable_mqtt:
            self.logger.warning("MQTT está deshabilitado. Conexión omitida.")
            return

        for broker in self.config["broker_addresses"]:
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

    def publish(self, topic, message):
        """
        Publica un mensaje en un tópico MQTT, agregando un ID único para trazabilidad.

        :param topic: Tópico al que se publicará el mensaje.
        :param message: Mensaje a publicar (en formato JSON).
        """
        if not self.enable_mqtt:
            self.logger.warning("MQTT está deshabilitado. Publicación omitida.")
            return

        try:
            # Agregar ID único al mensaje
            message_with_id = message.copy() if isinstance(message, dict) else {"message": message}
            message_with_id["id"] = str(uuid.uuid4())

            result = self.client.publish(topic, str(message_with_id))
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"[MQTT] Mensaje publicado en {topic}: {message_with_id}")
            else:
                self.logger.error(f"[MQTT] Error al publicar mensaje en {topic}: Código {result.rc}")
        except Exception as e:
            self.logger.error(f"[MQTT] Error publicando mensaje en {topic}: {e}")

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback ejecutado al conectarse al broker MQTT.
        """
        if rc == 0:
            self.logger.info("[MQTT] Conexión al broker establecida exitosamente.")
        else:
            self.logger.warning(f"[MQTT] Fallo en la conexión al broker, código: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """
        Callback ejecutado al desconectarse del broker MQTT.
        """
        if rc == 0:
            self.logger.info("[MQTT] Desconectado del broker.")
        else:
            self.logger.warning(f"[MQTT] Desconexión inesperada, código: {rc}")

    def on_publish(self, client, userdata, mid):
        """
        Callback ejecutado al completar una publicación.
        """
        self.logger.debug(f"[MQTT] Publicación completada con ID: {mid}")
