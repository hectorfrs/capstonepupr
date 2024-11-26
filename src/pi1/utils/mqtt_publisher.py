import json
import paho.mqtt.client as mqtt
import ssl

class MQTTPublisher:
    def __init__(self, endpoint, cert_path, key_path, ca_path):
        """
        Inicializa el cliente MQTT para conectarse a AWS IoT Core.

        :param endpoint: Endpoint de AWS IoT Core.
        :param cert_path: Ruta al certificado del cliente.
        :param key_path: Ruta a la llave privada del cliente.
        :param ca_path: Ruta al certificado CA raíz de AWS IoT.
        """
        self.endpoint = endpoint
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path
        self.client = mqtt.Client()

        # Configuración TLS para una conexión segura
        self.client.tls_set(
            ca_certs=self.ca_path,
            certfile=self.cert_path,
            keyfile=self.key_path,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
    
    def connect(self):
        """
        Conecta el cliente MQTT al endpoint de AWS IoT Core.
        """
        try:
            print(f"Connecting to AWS IoT Core at {self.endpoint}...")
            self.client.connect(self.endpoint, port=8883)
            print("Connected to AWS IoT Core.")
        except Exception as e:
            print(f"Failed to connect to AWS IoT Core: {e}")
            raise e
    
    def publish(self, topic, payload):
        """
        Publica un mensaje en el tópico MQTT especificado.

        :param topic: Tópico MQTT al cual publicar los datos.
        :param payload: Datos a publicar (deben ser serializables en JSON).
        """
        try:
            message = json.dumps(payload)
            print(f"Publishing to topic {topic}: {message}")
            self.client.publish(topic, message)
            print("Message published successfully.")
        except Exception as e:
            print(f"Failed to publish message: {e}")
            raise e
    
    def disconnect(self):
        """
        Desconecta el cliente MQTT del endpoint de AWS IoT Core.
        """
        try:
            print("Disconnecting from AWS IoT Core...")
            self.client.disconnect()
            print("Disconnected successfully.")
        except Exception as e:
            print(f"Failed to disconnect from AWS IoT Core: {e}")
            raise e
