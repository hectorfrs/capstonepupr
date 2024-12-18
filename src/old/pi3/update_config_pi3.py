import paho.mqtt.client as mqtt
import yaml
import json

# Cargar configuración desde config.yaml
with open("config/pi3_config.yaml", "r") as file:
    config = yaml.safe_load(file)

broker = config['mqtt']['broker_addresses'][0]
port = config['mqtt']['port']
username = config['mqtt']['username']
password = config['mqtt']['password']
topics = config['mqtt']['topics']

# Crear cliente MQTT
client = mqtt.Client()
client.username_pw_set(username, password)

# Conectar al broker
print(f"Conectando al broker MQTT en {broker}:{port}...")
client.connect(broker, port, keepalive=60)
print("Conexión establecida.")

# Publicar una actualización de configuración
def send_update(target, settings):
    topic = topics.get(f"settings_update_{target}")
    if not topic:
        print(f"Error: Tópico no encontrado para {target}")
        return

    update_message = {
        "settings": settings
    }

    client.publish(topic, json.dumps(update_message))
    print(f"Mensaje enviado a {topic}: {json.dumps(update_message)}")

# Ejemplo: Enviar actualizaciones a Raspberry Pi #1 y #2
send_update("pi1", {"read_interval": 5, "threshold": 20.5})
send_update("pi2", {"pressure_limit": 30, "control_mode": "automatic"})
