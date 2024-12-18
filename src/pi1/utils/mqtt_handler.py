#mqtt_handler.py es un módulo que proporciona una clase centralizada para manejar conexiones MQTT y la publicación de mensajes.
#Se utiliza la biblioteca paho-mqtt para la comunicación MQTT y el módulo logging para registrar eventos.

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
        self.logger = logging.getLogger("MQTTHandler")          # Logger personalizado
        self.config = config
        self.broker = config["broker_addresses"][0]             # Utilizar el primer broker como predeterminado
        self.port = config.get("port", 1883)
        self.keepalive = config.get("keepalive", 60)
        self.client_id = config.get("client_id", "MQTTClient")
        self.client = mqtt.Client(client_id=self.client_id)
        #self.username = config.get("username", None)
        #self.password = config.get("password", None)

        # Configuración de autenticación si es necesaria
        #if self.username and self.password:
            #self.client.username_pw_set(self.username, self.password)

        # Configuración de callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish

    def connect(self):
        """
        Intenta conectarse a cada dirección de broker hasta que tenga éxito.
        """
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
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.info("[MQTT] Desconectado del broker exitosamente.")
        except Exception as e:
            self.logger.error(f"[MQTT] Error al desconectar del broker: {e}")

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

    def publish_multiple(self, messages):
        """
        Publica múltiples mensajes en distintos tópicos.

        Args:
            messages (list): Lista de diccionarios con "topic" y "message".
        """
        for msg in messages:
            topic = msg.get("topic")
            message = msg.get("message")
            if topic and message:
                self.publish(topic, message)
            else:
                self.logger.warning(f"[MQTT] Mensaje inválido: {msg}")

    def subscribe(self, topics):
        """
        Suscribe el cliente MQTT a uno o más tópicos.

        Args:
            topics (str | list): Un tópico como string o una lista de tópicos.
        """
        try:
            if isinstance(topics, str):  # Si es un solo tópico
                self.client.subscribe(topics)
                self.logger.info(f"[MQTT] Suscrito al tópico: {topics}")
            elif isinstance(topics, list):  # Si es una lista de tópicos
                for topic in topics:
                    self.client.subscribe(topic)
                    self.logger.info(f"[MQTT] Suscrito al tópico: {topic}")
            else:
                self.logger.error(f"[MQTT] Tipo de datos no válido para suscripción: {type(topics)}")
        except Exception as e:
            self.logger.error(f"[MQTT] Error al suscribirse a los tópicos: {e}")


    def subscribe_multiple(self, topics_callbacks):
        """
        Se suscribe a múltiples tópicos con callbacks específicos.

        Args:
            topics_callbacks (dict): Diccionario donde las claves son tópicos y los valores son callbacks.
        """
        for topic, callback in topics_callbacks.items():
            self.client.message_callback_add(topic, callback)
            self.client.subscribe(topic)
            self.logger.info(f"[MQTT] Suscrito al tópico: {topic}")


    def enable_auto_reconnect(self):
        """
        Habilita la reconexión automática en caso de desconexión.
        """
        self.client.reconnect_delay_set(min_delay=1, max_delay=10)
        self.logger.info("[MQTT] Reconexión automática habilitada con retraso progresivo.")

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

    def is_connected(self):
        """
        Verifica si el cliente MQTT está conectado.

        Returns:
            bool: True si está conectado, False en caso contrario.
        """
        return self.client.is_connected()

    def on_publish(self, client, userdata, mid):
        """
        Callback ejecutado al completar una publicación.
        """
        self.logger.debug(f"[MQTT] Publicación completada con ID: {mid}")
    
    def forever_loop(self):
        """
        Mantiene el cliente MQTT en funcionamiento escuchando mensajes continuamente.
        El bucle se ejecuta hasta que se interrumpe manualmente (Ctrl+C).
        """
        try:
            self.logger.info("[MQTT] Iniciando bucle infinito para escuchar mensajes...")
            self.client.loop_forever()
        except KeyboardInterrupt:
            self.logger.info("[MQTT] Bucle infinito detenido manualmente (Ctrl+C).")
            self.disconnect()
        except Exception as e:
            self.logger.error(f"[MQTT] Error en el bucle infinito: {e}")
            self.disconnect()

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
    
    def backup_message(self, topic, message, backup_file="mqtt_backup.json"):
        """
        Almacena el mensaje localmente si no se puede publicar.

        Args:
            topic (str): Tópico del mensaje.
            message (str): Mensaje que se intentó enviar.
            backup_file (str): Ruta del archivo JSON para almacenar backups.
        """
        try:
            with open(backup_file, "a") as f:
                data = {"topic": topic, "message": message}
                f.write(json.dumps(data) + "\n")
            self.logger.warning(f"[MQTT] Mensaje almacenado localmente en {backup_file}: {data}")
        except Exception as e:
            self.logger.error(f"[MQTT] Error al almacenar mensaje localmente: {e}")

    def get_statistics(self):
        """
        Devuelve estadísticas del cliente MQTT.
        """
        stats = {
            "published": self.client._out_messages,
            "received": self.client._in_messages,
        }
        self.logger.info(f"[MQTT] Estadísticas: {stats}")
        return stats

    def publish_with_details(self, topic, message):
        """
        Publica un mensaje con detalles adicionales.
        """
        start_time = time.time()
        try:
            result = self.client.publish(topic, message)
            elapsed_time = time.time() - start_time
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"[MQTT] Mensaje publicado en {topic}: {message} (Tiempo: {elapsed_time:.2f} segundos)")
            else:
                self.logger.error(f"[MQTT] Error al publicar en {topic}. Código: {result.rc}")
        except Exception as e:
            self.logger.error(f"[MQTT] Error publicando mensaje: {e}")


