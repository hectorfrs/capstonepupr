import paho.mqtt.client as mqtt
import yaml
import json

# Función para manejar mensajes recibidos
def on_message(client, userdata, msg):
    print(f"Mensaje recibido en {msg.topic}: {msg.payload.decode()}")
    try:
        update = json.loads(msg.payload.decode())
        settings = update.get("settings")
        if settings:
            print("Actualizando configuración...")
            with open("config/pi2_config.yaml", "r") as file:
                config = yaml.safe_load(file)
            config.update(settings)
            with open("config/pi2_config.yaml", "w") as file:
                yaml.dump(config, file)
            print("Configuración actualizada exitosamente.")
        else:
            print("El mensaje no contiene configuraciones válidas.")
    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")

# Cargar configuración desde config.yaml
with open("config/pi2_config.yaml", "r") as file:
    config = yaml.safe_load(file)

broker = config['mqtt']['broker_addresses'][0]
port = config['mqtt']['port']
username = config['mqtt']['username']
password = config['mqtt']['password']
topic = config['mqtt']['topics']['settings_update_pi2']

# Crear cliente MQTT
client = mqtt.Client()
client.username_pw_set(username, password)
client.on_message = on_message

# Conectar al broker
print(f"Conectando al broker MQTT en {broker}:{port}...")
client.connect(broker, port, keepalive=60)
print("Conexión establecida.")

# Suscribirse al tópico
client.subscribe(topic)
print(f"Suscrito al tópico {topic}")

# Mantener el cliente en bucle para recibir mensajes
client.loop_forever()
