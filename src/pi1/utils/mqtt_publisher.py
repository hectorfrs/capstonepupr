import json
import paho.mqtt.client as mqtt  # Librería MQTT para la publicación

class MqttPublisher:
    def __init__(self, topic):
        """
        Inicializa el publicador MQTT con un tópico específico para AWS IoT Core.
        
        :param topic: El tópico de AWS IoT Core donde se publicarán los datos.
        """
        self.topic = topic

    def publish(self, data):
        """
        Publica los datos al tópico MQTT en AWS IoT Core.
        
        :param data: Los datos que serán enviados a AWS IoT Core.
        """
        # Parámetros del endpoint de AWS IoT
        endpoint = "your_aws_iot_core_endpoint"  # Reemplazar por el endpoint real de AWS IoT Core
        port = 8883  # Puerto seguro para MQTT

        # Certificados para autenticación segura
        ca_path = "/certs/AmazonRootCA1.pem"
        cert_path = "/certs/certificate.pem.crt"
        key_path = "/certs/private.pem.key"

        # Crear un cliente MQTT
        client = mqtt.Client()

        # Configurar el cliente para usar TLS con los certificados
        client.tls_set(ca_certs=ca_path, certfile=cert_path, keyfile=key_path)

        # Conectar al endpoint de AWS IoT Core
        client.connect(endpoint, port=port)

        # Convertir los datos a formato JSON
        payload = json.dumps(data)
        print(f"Publishing data to topic {self.topic}: {payload}")

        # Publicar los datos en el tópico especificado
        client.publish(self.topic, payload)

        # Cerrar la conexión MQTT
        client.disconnect()
        print("Data published and connection closed.")
