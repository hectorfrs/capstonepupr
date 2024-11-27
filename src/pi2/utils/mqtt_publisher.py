import json
import paho.mqtt.client as mqtt
import ssl


class MQTTPublisher:
    """
    Clase para manejar conexiones y publicaciones MQTT, soportando redundancia de endpoints.
    """
    def __init__(self, endpoints, cert_path=None, key_path=None, ca_path=None, local=False):
        """
        Inicializa el cliente MQTT.

        :param endpoints: Lista de endpoints del broker MQTT (local o AWS IoT Core).
        :param cert_path: Ruta al certificado del cliente (para AWS IoT Core).
        :param key_path: Ruta a la llave privada del cliente (para AWS IoT Core).
        :param ca_path: Ruta al certificado CA raíz de AWS IoT (para AWS IoT Core).
        :param local: Indica si es una conexión local (sin TLS).
        """
        self.endpoints = endpoints if isinstance(endpoints, list) else [endpoints]
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path
        self.local = local
        self.client = mqtt.Client()

        if not local:
            # Configuración TLS para AWS IoT Core
            self.client.tls_set(
                ca_certs=self.ca_path,
                certfile=self.cert_path,
                keyfile=self.key_path,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )
    
    def connect(self, port=8883):
        """
        Conecta el cliente MQTT al primer endpoint disponible.

        :param port: Puerto del broker MQTT (por defecto 8883 para AWS IoT Core).
        """
        for endpoint in self.endpoints:
            try:
                print(f"Intentando conectar a {'broker local' if self.local else 'AWS IoT Core'} en {endpoint}:{port}...")
                self.client.connect(endpoint, port=port)
                print(f"Conexión exitosa a {endpoint}:{port}")
                return  # Salir si la conexión es exitosa
            except Exception as e:
                print(f"Fallo al conectar con {endpoint}:{port} - {e}")

        # Si no se pudo conectar a ningún endpoint
        raise ConnectionError("No se pudo conectar a ninguno de los endpoints proporcionados.")
    
    def publish(self, topic, payload):
        """
        Publica un mensaje en el tópico MQTT especificado.

        :param topic: Tópico MQTT al cual publicar los datos.
        :param payload: Datos a publicar (deben ser serializables en JSON).
        """
        try:
            message = json.dumps(payload)
            print(f"Publicando en el tópico {topic}: {message}")
            self.client.publish(topic, message)
            print("Mensaje publicado exitosamente.")
        except Exception as e:
            print(f"Fallo al publicar el mensaje: {e}")
            raise e
    
    def disconnect(self):
        """
        Desconecta el cliente MQTT del broker.
        """
        try:
            print(f"Desconectando de {'broker local' if self.local else 'AWS IoT Core'}...")
            self.client.disconnect()
            print("Desconexión exitosa.")
        except Exception as e:
            print(f"Fallo al desconectar del broker: {e}")
            raise e
