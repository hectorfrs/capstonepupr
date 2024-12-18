import json
import paho.mqtt.client as mqtt
import ssl

def send_data_to_aws(endpoint, topic, payload, cert_path, key_path, ca_path):
    """
    Publica datos a AWS IoT Core utilizando MQTT.
    
    :param endpoint: Endpoint de AWS IoT Core.
    :param topic: Tópico MQTT al cual publicar los datos.
    :param payload: Datos a publicar (deben ser serializables en JSON).
    :param cert_path: Ruta al certificado del cliente.
    :param key_path: Ruta a la llave privada del cliente.
    :param ca_path: Ruta al certificado CA raíz de AWS IoT.
    """
    # Configuración del cliente MQTT
    client = mqtt.Client()
    client.tls_set(
        ca_certs=ca_path,
        certfile=cert_path,
        keyfile=key_path,
        tls_version=ssl.PROTOCOL_TLSv1_2
    )

    # Conectar al endpoint de AWS IoT Core
    print(f"Connecting to AWS IoT Core at {endpoint}...")
    client.connect(endpoint, port=8883)
    print("Connected to AWS IoT Core.")

    # Publicar los datos
    message = json.dumps(payload)
    print(f"Publishing to topic {topic}: {message}")
    client.publish(topic, message)
    print("Data published successfully.")
    
    # Finalizar la conexión MQTT
    client.disconnect()
    print("Disconnected from AWS IoT Core.")
