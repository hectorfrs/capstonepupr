import paho.mqtt.client as mqtt
import yaml
import json

# Función para manejar comandos de control de válvulas
def on_message(client, userdata, msg):
    print(f"Mensaje recibido en {msg.topic}: {msg.payload.decode()}")
    try:
        command = json.loads(msg.payload.decode())
        valve = command.get("valve")
        action = command.get("action")
        if valve and action:
            print(f"Ejecutando comando para {valve}: {action}")
            # Aquí se incluiría la lógica para controlar las válvulas
            # Por ejemplo: activar o desactivar relés
        else:
            print("El mensaje no contiene comandos válidos.")
    except Exception as e:
        print(f"Error al procesar el comando: {e}")

# Cargar configuración desde config.yaml
with open("config/pi2_config.yaml", "r") as file:
    config = yaml.safe_load(file)

broker = config['mqtt']['broker_addresses'][0]
port = config['mqtt']['port']
username = config['mqtt']['username']
password = config['mqtt']['password']
topic = config['mqtt']['topics']['valve_control']

# Crear cliente MQTT
client = mqtt.Client()
client.username_pw_set(username, password)
client.on_message = on_message

# Conectar al broker
print(f"Conectando al broker MQTT en {broker}:{port}...")
client.connect(broker, port, keepalive=60)
print("Conexión establecida.")

# Suscribirse al tópico de control de válvulas
client.subscribe(topic)
print(f"Suscrito al tópico {topic}")

# Mantener el cliente en bucle para recibir comandos
client.loop_forever()
