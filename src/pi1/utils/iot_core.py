import json
import paho.mqtt.client as mqtt  # Librería MQTT

def send_data_to_aws(endpoint, topic, data, cert_path, key_path, ca_path):
    print(f"Connecting to AWS IoT Core at {endpoint} using MQTT with TLS...")

    # Configurar el cliente MQTT
    client = mqtt.Client()

    # Agregar los certificados para la autenticación
    client.tls_set(ca_certs=ca_path,   # Certificado de AWS IoT Root CA
                   certfile=cert_path, # Certificado del cliente
                   keyfile=key_path,   # Llave privada del cliente
                   tls_version=2)      # Versión de TLS (segura)

    # Conectar al endpoint MQTT de AWS IoT Core
    client.connect(endpoint, port=8883)  # Puerto seguro para MQTT con TLS
    
    # Publicar los datos en el tópico de AWS IoT
    payload = json.dumps(data)
    print(f"Publishing to {topic}: {payload}")
    client.publish(topic, payload)
    client.disconnect()
    print("Data sent and connection closed.")
