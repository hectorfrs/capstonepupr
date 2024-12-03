import paho.mqtt.client as mqtt
import ssl
import yaml
import time
from threading import Thread


class MQTTPublisher:
    """
    Clase para manejar la conexión y publicación en un broker MQTT.
    Soporta un broker local y AWS IoT Core.
    """

    def __init__(self, config_path="config/pi2_config.yaml", use_aws=False, local=None):
        """
        Inicializa el cliente MQTT usando la configuración YAML.

        :param config_path: Ruta al archivo de configuración YAML.
        :param use_aws: Booleano para indicar si se debe conectar a AWS IoT Core.
        """
        self.config = self.load_config(config_path)

        # Si `local` está especificado, sobreescribe `use_aws`
        self.use_aws = not local if local is not None else use_aws

        # Configuración del broker MQTT
        if self.use_aws:
            self.broker = self.config['aws']['iot_core_endpoint']
            self.port = 8883
            self.cert_path = self.config['aws']['cert_path']
            self.key_path = self.config['aws']['key_path']
            self.ca_path = self.config['aws']['ca_path']
        else:
            self.broker = self.config['mqtt']['broker_addresses'][0]
            self.port = self.config['mqtt']['port']
            self.username = self.config['mqtt'].get('username')
            self.password = self.config['mqtt'].get('password')

        # Inicializar cliente MQTT
        self.client = mqtt.Client()
        self.configure_client()

    @staticmethod
    def load_config(config_path):
        """
        Carga la configuración desde un archivo YAML.

        :param config_path: Ruta al archivo YAML.
        :return: Diccionario con la configuración cargada.
        """
        with open(config_path, "r") as file:
            return yaml.safe_load(file)

    def configure_client(self):
        """
        Configura el cliente MQTT para el broker local o AWS IoT Core.
        """
        if self.use_aws:
            # Configurar TLS para AWS IoT Core
            self.client.tls_set(
                ca_certs=self.ca_path,
                certfile=self.cert_path,
                keyfile=self.key_path,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )
            print(f"Cliente MQTT configurado para AWS IoT Core: {self.broker}")
        else:
            # Configurar autenticación para el broker local
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            print(f"Cliente MQTT configurado para broker local: {self.broker}")

    def connect(self):
        """
        Conecta al broker MQTT.
        """
        try:
            print(f"Intentando conectar al broker MQTT {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            print("Conexión al broker MQTT exitosa.")
        except Exception as e:
            print(f"Error al conectar con el broker MQTT: {e}")

    def publish_parallel(self, topic, message):
        """
        Publica un mensaje en un tópico MQTT usando un hilo.

        :param topic: Tópico donde publicar el mensaje.
        :param message: Mensaje a publicar.
        """
        thread = Thread(target=self.publish, args=(topic, message))
        thread.start()

    def publish(self, topic, message):
        """
        Publica un mensaje en un tópico MQTT.

        :param topic: Tópico donde publicar el mensaje.
        :param message: Mensaje a publicar.
        """
        try:
            self.client.publish(topic, message)
            print(f"Mensaje publicado en {topic}: {message}")
        except Exception as e:
            print(f"Error al publicar mensaje en {topic}: {e}")

    def subscribe(self, topic, callback):
        """
        Se suscribe a un tópico MQTT y establece un callback.

        :param topic: Tópico al que suscribirse.
        :param callback: Función callback para manejar mensajes recibidos.
        """
        def on_message(client, userdata, msg):
            print(f"Mensaje recibido en {msg.topic}: {msg.payload.decode()}")
            callback(msg)

        self.client.on_message = on_message
        self.client.subscribe(topic)
        print(f"Suscrito al tópico: {topic}")

    def loop_forever(self):
        """
        Inicia el bucle de mensajes del cliente MQTT.
        """
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("Desconectando del cliente MQTT...")
            self.client.disconnect()
