import paho.mqtt.client as mqtt
import logging

class MQTTHandler:
    """
    Clase centralizada para manejar conexiones MQTT y la publicación de mensajes.
    """

    def __init__(self, config):
        """
        Inicializa la clase MQTTHandler con la configuración proporcionada.
        
        Args:
            config (dict): Configuración para el cliente MQTT.
        """
        self.logger = logging.getLogger("MQTTHandler")
        self.config = config
        self.broker = config["broker_addresses"][0]  # Utilizar el primer broker como predeterminado
        self.port = config.get("port", 1883)
        #self.username = config.get("username", None)
        #self.password = config.get("password", None)
        self.client = mqtt.Client()

        # Configuración de autenticación si es necesaria
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        # Callbacks opcionales
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish

    def connect(self):
        """
        Conecta al broker MQTT.
        """
        try:
            self.logger.info(f"[MQTT] Intentando conectar al broker {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port)
            self.client.loop_start()  # Inicia el loop de la biblioteca MQTT
            self.logger.info("[MQTT] Conexión al broker exitosa.")
        except Exception as e:
            self.logger.critical(f"[MQTT] Error conectando al broker: {e}")

    def disconnect(self):
        """
        Desconecta del broker MQTT.
        """
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.info("[MQTT] Desconectado del broker exitosamente.")
        except Exception as e:
            self.logger.error(f"[MQTT] Error desconectando del broker: {e}")

    def publish(self, topic, message):
        """
        Publica un mensaje en un tópico MQTT.

        Args:
            topic (str): Tópico al que se publicará el mensaje.
            message (str): Mensaje a publicar.
        """
        try:
            result = self.client.publish(topic, message)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"[MQTT] Mensaje publicado en {topic}: {message}")
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
    
    def loop_forever(self):
        """Inicia el bucle principal de MQTT para manejar la comunicación."""
        try:
            logging.info("[MQTT] Iniciando bucle MQTT...")
            self.client.loop_forever()
        except KeyboardInterrupt:
            logging.info("[MQTT] Interrumpido manualmente. Finalizando bucle.")
            self.client.disconnect()
    
    def disconnect(self):
        """
        Desconecta el cliente MQTT.
        """
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logging.info("[MQTT] Cliente MQTT desconectado exitosamente.")
        except Exception as e:
            logging.error(f"[MQTT] Error al desconectar el cliente MQTT: {e}")
