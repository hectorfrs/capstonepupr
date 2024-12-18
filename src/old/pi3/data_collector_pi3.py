import paho.mqtt.client as mqtt
import yaml
import json

# Función para manejar mensajes recibidos
def on_message(client, userdata, msg):
    print(f"Mensaje recibido en {msg.topic}: {msg.payload.decode()}")
    try:
        data = json.loads(msg.payload.decode())
        # Aquí puedes procesar y combinar datos recibidos de Raspberry Pi #1 y #2
        print(f"Procesando datos: {data}")
    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")

# Cargar configuración desde config.yaml
with open("config/pi3_config.yaml", "r") as file:
    config = yaml.safe_load(file)

broker = config['mqtt']['broker_addresses'][0]
port = config['mqtt']['port']
username = config['mqtt']['username']
password = config['mqtt']['password']
topics = [config['mqtt']['topics']['sensor_data_pi1'], config['mqtt']['topics']['sensor_data_pi2']]

# Crear cliente MQTT
client = mqtt.Client()
client.username_pw_set(username, password)

# Asignar función callback
client.on_message = on_message

# Conectar al broker
print(f"Conectando al broker MQTT en {broker}:{port}...")
client.connect(broker, port, keepalive=60)
print("Conexión establecida.")

# Suscribirse a los tópicos de datos de sensores
for topic in topics:
    client.subscribe(topic)
    print(f"Suscrito al tópico {topic}")

# Mantener cliente en bucle para recibir mensajes
client.loop_forever()
