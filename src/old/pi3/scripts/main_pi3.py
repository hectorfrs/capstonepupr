# main.py - Script principal para Raspberry Pi #3
# Desarrollado por Héctor F. Rivera Santiago
# copyright (c) 2024

# Raspberry Pi #3 (Registro y Publicación a la Nube)

import yaml
import logging
import os
from utils.mqtt_publisher import MQTTPublisher
from utils.greengrass import process_with_greengrass
from lib.weight_sensor import WeightSensor
from lib.camera import Camera
import tkinter as tk


def load_config():
    """
    Carga la configuración desde el archivo YAML.
    """
    print("Cargando configuración para Raspberry Pi 3...")
    config_path = 'config/pi3_config.yaml'
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"No se encontró el archivo de configuración en {config_path}")
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    print("Configuración cargada.")
    return config


def on_sensor_data(client, userdata, message):
    """
    Callback para manejar datos recibidos de Raspberry Pi #1 y #2.
    """
    print(f"Mensaje recibido en tópico {message.topic}: {message.payload}")
    data = json.loads(message.payload)
    # Procesar datos según el tópico
    if message.topic == config['mqtt']['topics']['sensor_data_pi1']:
        print(f"Procesando datos de Pi1: {data}")
    elif message.topic == config['mqtt']['topics']['sensor_data_pi2']:
        print(f"Procesando datos de Pi2: {data}")


def send_settings_to_pi(pi_number, settings):
    """
    Envía configuraciones específicas a Raspberry Pi #1 o #2.

    :param pi_number: Número de Raspberry Pi (1 o 2).
    :param settings: Configuraciones en formato JSON.
    """
    topic = config['mqtt']['topics'][f'settings_update_pi{pi_number}']
    mqtt_publisher.publish(topic, settings)
    print(f"Configuraciones enviadas a Raspberry Pi #{pi_number} en el tópico {topic}: {settings}")


def create_touch_screen_menu():
    """
    Crea un menú interactivo en la pantalla táctil.
    """
    def adjust_valves():
        print("Ajustando configuraciones de válvulas...")
        send_settings_to_pi(1, {"action": "adjust_valves"})
        send_settings_to_pi(2, {"action": "adjust_valves"})

    def calibrate_sensors():
        print("Calibrando sensores...")
        send_settings_to_pi(1, {"action": "calibrate_sensors"})
        send_settings_to_pi(2, {"action": "calibrate_sensors"})

    def start_camera_analysis():
        print("Iniciando análisis de cámara...")
        process_with_greengrass(config['greengrass']['functions'][1]['arn'], {"action": "start"})

    def stop_camera_analysis():
        print("Deteniendo análisis de cámara...")
        process_with_greengrass(config['greengrass']['functions'][1]['arn'], {"action": "stop"})

    def view_system_status():
        print("Mostrando estado del sistema...")
        # Aquí puedes implementar detalles específicos del estado del sistema.

    root = tk.Tk()
    root.title("Control de Raspberry Pi")

    tk.Button(root, text="Ajustar Configuración de Válvulas", command=adjust_valves).pack(pady=10)
    tk.Button(root, text="Calibrar Sensores", command=calibrate_sensors).pack(pady=10)
    tk.Button(root, text="Iniciar Análisis de Cámara", command=start_camera_analysis).pack(pady=10)
    tk.Button(root, text="Detener Análisis de Cámara", command=stop_camera_analysis).pack(pady=10)
    tk.Button(root, text="Estado del Sistema", command=view_system_status).pack(pady=10)
    tk.Button(root, text="Salir", command=root.quit).pack(pady=10)

    root.mainloop()


def main():
    """
    Función principal para manejar datos de peso, cámara y comunicación.
    """
    global config
    config = load_config()

    # Configurar logging
    logging.basicConfig(filename=config['logging']['log_file'], level=logging.INFO)
    print("Logging configurado.")

    # Inicializar sensor de peso y cámara
    weight_sensor = WeightSensor(
        i2c_address=config['weight_sensor']['i2c_address'],
        calibration_factor=config['weight_sensor']['calibration_factor']
    )
    camera = Camera(
        resolution=config['camera']['resolution'],
        frame_rate=config['camera']['frame_rate']
    )

    # Configurar cliente MQTT para publicación en AWS IoT Core
    aws_publisher = MQTTPublisher(
        endpoints=config['aws']['iot_core_endpoint'],
        cert_path=config['aws']['cert_path'],
        key_path=config['aws']['key_path'],
        ca_path=config['aws']['ca_path']
    )
    aws_publisher.connect()

    # Crear cliente MQTT para comunicación local
    local_publisher = MQTTPublisher(endpoints=["localhost"], local=True)
    local_publisher.connect(port=config['mqtt']['broker']['port'])

    # Ejecutar el menú táctil
    create_touch_screen_menu()


if __name__ == '__main__':
    main()
