import paho.mqtt.client as mqtt
import ssl
import time
import yaml
from threading import Thread
from logging_manager import FunctionMonitor


class MQTTPublisher:
    """
    Clase para manejar la conexión y publicación en un broker MQTT.
    Soporta un broker local y AWS IoT Core.
    """

    def __init__(self, config, local=True):
        """
        Inicializa el cliente MQTT usando la configuración YAML.

        :param config_path: Ruta al archivo de configuración YAML.
        :param local: Booleano que indica si se usará el broker local (True) o AWS IoT Core (False).
        """
        #self.config = self.load_config(config_path)
        self.config = config

        # Configuración del broker MQTT
        if local:
            self.broker = self.config['mqtt']['broker_address'][0]  # Tomar el primer broker como predeterminado
            self.port = self.config['mqtt']['port']
            self.username = self.config['mqtt']['username']
            self.password = self.config['mqtt']['password']
        else:
            self.broker = self.config['aws']['iot_core_endpoint']
            self.port = 8883
            self.cert_path = self.config['aws']['cert_path']
            self.key_path = self.config['aws']['key_path']
            self.ca_path = self.config['aws']['ca_path']

        # Inicializar cliente MQTT
        self.client = mqtt.Client()
        self.configure_client(local)

    @staticmethod
    def load_config(config_path):
        """
        Carga la configuración desde un archivo YAML.

        :param config_path: Ruta al archivo YAML.
        :return: Diccionario con la configuración cargada.
        """
        with open(config_path, "r") as file:
            return yaml.safe_load(file)

    def configure_client(self, local):
        """
        Configura el cliente MQTT según el tipo de broker.

        :param local: Booleano que indica si es un broker local o AWS IoT Core.
        """
        if local:
            self.client.username_pw_set(self.username, self.password)
            logging.info(f"[MQTT] Cliente configurado para broker local: {self.broker}")
        else:
            self.client.tls_set(
                ca_certs=self.ca_path,
                certfile=self.cert_path,
                keyfile=self.key_path
            )
            logging.info(f"[MQTT] Cliente configurado para AWS IoT Core: {self.broker}")

    def connect(self):
        try:
            logging.info(f"[MQTT] Intentando conectar al broker {self.broker} en el puerto {self.port}...")
            self.client.connect(self.broker, self.port, keepalive=60)
            logging.info("[MQTT] Conexión al broker exitosa.")
        except Exception as e:
            logging.info(f"[MQTT] Error al conectar con el broker: {e}")
            for i in range(3):  # Intenta reconectar hasta 3 veces
                time.sleep(5)
                try:
                    self.client.connect(self.broker, self.port, keepalive=60)
                    logging.info("[MQTT] Conexión al broker MQTT exitosa en reintento.")
                    return
                except Exception as retry_error:
                    logging.info(f"[MQTT] Reintento {i+1} fallido: {retry_error}")
            raise ConnectionError(f"[MQTT] No se pudo conectar con el broker MQTT después de 3 intentos: {e}")

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
            logging.info(f"[MQTT] Mensaje publicado en {topic}: {message}")
        except Exception as e:
            logging.error(f"[MQTT] Error al publicar mensaje en {topic}: {e}")
            raise

    def subscribe(self, topic, callback):
        """
        Se suscribe a un tópico MQTT y establece un callback.

        :param topic: Tópico al que suscribirse.
        :param callback: Función callback para manejar mensajes recibidos.
        """
        def on_message(client, userdata, msg):
            logging.info(f"[MQTT] Mensaje recibido en {msg.topic}: {msg.payload.decode()}")
            callback(msg)

        self.client.on_message = on_message
        self.client.subscribe(topic)
        logging.info(f"[MQTT] Suscrito al tópico: {topic}")

    def loop_forever(self):
        """
        Inicia el bucle de mensajes del cliente MQTT.
        """
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            logging.warning("[MQTT] Desconectando del cliente MQTT...")
            self.client.disconnect()

# # Ejemplo de uso:

# # Publicar datos paralelamante en un tópico MQTT
# from utils.mqtt_publisher import MQTTPublisher

# def main():
#     # Inicializar cliente MQTT para el broker local
#     mqtt_client = MQTTPublisher(config_path="config/pi1_config.yaml", local=True)

#     # Conectar al broker
#     mqtt_client.connect()

#     # Publicar múltiples mensajes en paralelo
#     for i in range(5):
#         topic = "pi1/sensor_data"
#         message = f'{{"id": {i}, "detected_material": "PET"}}'
#         mqtt_client.publish_parallel(topic, message)

# if __name__ == "__main__":
#     main()

# # Suscribirse a un tópico MQTT
# from utils.mqtt_publisher import MQTTPublisher

# def message_callback(msg):
#     print(f"Mensaje procesado: {msg.payload.decode()}")

# def main():
#     mqtt_client = MQTTPublisher(config_path="config/pi1_config.yaml", local=True)
#     mqtt_client.connect()
#     mqtt_client.subscribe("pi1/settings_update", message_callback)
#     mqtt_client.loop_forever()

# if __name__ == "__main__":
#     main()
