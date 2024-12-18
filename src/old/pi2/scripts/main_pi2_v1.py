import yaml
import logging
import time

from datetime import datetime
from utils.json_manager import generate_json, save_json
from lib.valve_control import ValveControl
from lib.pressure_sensor import PressureSensorManager
from utils.mqtt_publisher import MQTTPublisher
from utils.json_logger import log_detection

import sys
import os
# Añadir el directorio principal de src/pi2 al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

def configure_logging(config):
    log_file = os.path.expanduser(config['logging']['log_file'])  # Expande '~' al directorio del usuario
    log_dir = os.path.dirname(log_file)

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    print(f"Logging configurado en {log_file}.")

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

def read_pressure(config):
    """
    Simula la lectura de sensores de presión utilizando los datos de configuración.
    """
    pressure_data = []
    for sensor in config["pressure_sensors"]["sensors"]:
        # Simular lectura de presión (valores aleatorios o calculados)
        simulated_pressure = 15.2  # PSI Simulado
        pressure_data.append({
            "sensor_name": sensor["name"],
            "i2c_address": sensor["i2c_address"],
            "pressure": simulated_pressure,
            "status": "OK" if config["pressure_sensors"]["min_pressure"] <= simulated_pressure <= config["pressure_sensors"]["max_pressure"] else "ALERT"
        })
    return pressure_data

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

    print("Iniciando monitoreo de presión...")

    # Leer presión desde los sensores configurados
    pressure_readings = read_pressure(config)

    # Formatear los datos para el log
    log_data = {
        "device_id": config["network"]["ethernet"]["ip"],  # Dirección IP del dispositivo
        "timestamp": datetime.now().isoformat(),
        "readings": pressure_readings
    }

    print(f"Lecturas registradas: {log_data}")

    # Registrar datos de presión
    log_detection(log_data, config_path="/home/raspberry-2/capstone/src/pi2/config/pi2_config.yaml")

if __name__ == "__main__":
    main()
