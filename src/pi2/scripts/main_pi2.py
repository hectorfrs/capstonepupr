import yaml
import logging
import sys
import os
# Añadir el directorio principal de src/pi2 al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import time
from utils.json_manager import ConfigManager
from lib.valve_control import ValveControl
from lib.pressure_sensor import PressureSensorManager
from utils.mqtt_publisher import MQTTPublisher
import time

def handle_valve_control(msg):
    """
    Callback para manejar comandos de control de válvulas recibidos a través de MQTT.
    """
    try:
        command = json.loads(msg.payload.decode("utf-8"))
        action = command.get("action")
        valve_id = command.get("valve_id")
        duration = command.get("duration", config['valves']['default_timeout'])

        if action == "activate":
            print(f"Activating valve {valve_id} for {duration} seconds.")
            valve_control.activate_valve(valve_id, duration)
        else:
            print(f"Unknown action: {action}")
    except Exception as e:
        print(f"Error processing valve control command: {e}")

def main():
    """
    Script principal para el manejo de sensores, válvulas y comunicación MQTT.
    """
    global config, valve_control, sensor_manager

    # Cargar configuración
    config_manager = ConfigManager("config/pi2_config.yaml")
    config = config_manager.config

    # Inicializar módulos
    valve_control = ValveControl(config['valves']['relay_module']['addresses'])
    sensor_manager = PressureSensorManager(config['pressure_sensors']['sensors'])
    mqtt = MQTTPublisher(config_path="config/pi2_config.yaml")

    # Conectar a MQTT
    mqtt.connect()

    # Suscribirse al tópico de control de válvulas
    mqtt.subscribe(config['mqtt']['topics']['valve_control'], handle_valve_control)

    try:
        # Bucle principal
        while True:
            # Leer sensores y publicar datos
            sensor_readings = sensor_manager.read_all_sensors()
            for reading in sensor_readings:
                mqtt.publish(
                    config['mqtt']['topics']['pressure_data'],
                    {"sensor": reading['name'], "pressure": reading['pressure']}
                )

            # Intervalo de tiempo entre lecturas
            time.sleep(config['pressure_sensors'].get('read_interval', 5))
    except KeyboardInterrupt:
        print("Apagando el sistema...")
        valve_control.cleanup()
        mqtt.client.disconnect()

if __name__ == "__main__":
    main()
