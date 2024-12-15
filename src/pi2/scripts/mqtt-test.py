import paho.mqtt.client as mqtt

# Configuración MQTT
BROKER_ADDRESS = "192.168.1.147"
PORT = 1883
USERNAME = "raspberry-2"
PASSWORD = "Elefante"

# Callback al conectar
def on_connect(client, userdata, flags, rc):
    print(f"Conectado al broker MQTT con código {rc}")
    client.subscribe("raspberry-2/settings_update")  # Suscribirse a un tópico

# Callback al recibir un mensaje
def on_message(client, userdata, msg):
    print(f"Mensaje recibido: {msg.topic} -> {msg.payload.decode()}")

# Configuración del cliente MQTT
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

# Conexión al broker
client.connect(BROKER_ADDRESS, PORT)

# Publicar un mensaje
client.publish("raspberry-2/sensor_data", "Test desde Raspberry Pi 2")

# Loop infinito
client.loop_forever()
