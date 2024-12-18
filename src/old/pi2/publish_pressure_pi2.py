import paho.mqtt.client as mqtt
import yaml
import json

# Cargar configuración desde config.yaml
with open("config/pi2_config.yaml", "r") as file:
    config = yaml.safe_load(file)

broker = config['mqtt']['broker_addresses'][0]
port = config['mqtt']['port']
username = config['mqtt']['username']
password = config['mqtt']['password']
topic = config['mqtt']['topics']['sensor_data_pi2']

# Crear cliente MQTT
client = mqtt.Client()
client.username_pw_set(username, password)

# Conectar al broker
print(f"Conectando al broker MQTT en {broker}:{port}...")
client.connect(broker, port, keepalive=60)
print("Conexión establecida.")

# Publicar un mensaje de ejemplo
data_message = {
    "sensor": "valve_1_inlet",
    "pressure": 12.3
}
client.publish(topic, json.dumps(data_message))
print(f"Mensaje publicado en el tópico {topic}: {json.dumps(data_message)}")
