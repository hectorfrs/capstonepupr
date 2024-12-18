import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conexión exitosa al broker MQTT")
        client.subscribe("raspberry-2/settings_update")  # Suscripción al conectar
    else:
        print(f"Error al conectar al broker MQTT. Código: {rc}")

def on_message(client, userdata, msg):
    print(f"Mensaje recibido: {msg.topic} -> {msg.payload.decode()}")

client = mqtt.Client(client_id="raspberry-2-client")
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect("192.168.1.147", 1883, 60)
    client.loop_forever()
except Exception as e:
    print(f"Error en la conexión MQTT: {e}")
