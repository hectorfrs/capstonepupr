import threading
import time
import yaml
import os
import logging

# Importar módulos personalizados
from lib.touch_screen_interface import TouchScreenInterface
from utils.greengrass import process_with_greengrass
from lib.weight_sensor import WeightSensor
from lib.camera_module import CameraModule
from utils.iot_core import IoTCoreClient

def load_config():
    """
    Carga la configuración desde el archivo YAML.
    """
    config_path = 'config/pi3_config.yaml'
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Archivo de configuración no encontrado en {config_path}")
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    print("Configuración cargada.")
    return config

def main():
    """
    Función principal para coordinar las operaciones de Raspberry Pi 3.
    """
    # Cargar la configuración
    config = load_config()

    # Configurar logging
    logging.basicConfig(filename=config['logging']['log_file'], level=logging.INFO)
    print("Logging configurado.")

    # Inicializar cliente MQTT para AWS IoT Core
    iot_client = IoTCoreClient(
        endpoint=config['aws']['iot_core_endpoint'],
        cert_path=config['aws']['cert_path'],
        key_path=config['aws']['key_path'],
        ca_path=config['aws']['ca_path']
    )
    iot_client.connect()
    iot_client.loop_start()

    # Inicializar sensor de peso
    weight_sensor_config = config['weight_sensor']
    weight_sensor = WeightSensor(
        i2c_bus=1,
        i2c_address=int(weight_sensor_config['i2c_address'], 16),
        calibration_factor=weight_sensor_config['calibration_factor']
    )
    # Realizar tara al iniciar
    weight_sensor.tare()

    # Inicializar módulo de cámara
    camera_module = CameraModule(config_path='config/pi3_config.yaml')

    # Inicializar interfaz táctil y pasar referencias de los sensores
    touch_screen_interface = TouchScreenInterface(
        weight_sensor=weight_sensor,
        camera_module=camera_module,
        iot_client=iot_client,
        config=config
    )

    # Iniciar hilos para lectura del sensor de peso y captura de cámara
    weight_thread = threading.Thread(target=read_weight_sensor, args=(weight_sensor, iot_client, config))
    weight_thread.daemon = True
    weight_thread.start()

    camera_thread = threading.Thread(target=stream_camera, args=(camera_module, iot_client, config))
    camera_thread.daemon = True
    camera_thread.start()

    # Ejecutar la interfaz táctil
    touch_screen_interface.run()

    # Al cerrar la interfaz, detener hilos y limpiar recursos
    camera_module.stop_video_stream()
    camera_module.release_camera()
    iot_client.loop_stop()
    print("Programa finalizado.")

def read_weight_sensor(weight_sensor, iot_client, config):
    """
    Lee continuamente el sensor de peso y publica datos en AWS IoT Core.
    """
    try:
        while True:
            weight = weight_sensor.get_weight()
            if weight is not None:
                # Procesar datos con Greengrass
                process_with_greengrass(config['greengrass']['group_name'], {'weight': weight})
                # Publicar datos en AWS IoT Core
                payload = {
                    'device': 'Raspberry Pi 3',
                    'weight': weight
                }
                iot_client.publish(config['aws']['iot_topics']['data_publish'], payload)
                print(f"Datos de peso publicados: {payload}")
            time.sleep(1)  # Ajustar el intervalo de lectura según sea necesario
    except Exception as e:
        logging.error(f"Error al leer el sensor de peso: {e}")

def stream_camera(camera_module, iot_client, config):
    """
    Captura imágenes de la cámara y publica resultados de análisis en AWS IoT Core.
    """
    try:
        while True:
            if camera_module.streaming:
                frame = camera_module.capture_image()
                if frame is not None:
                    analysis_result = camera_module.analyze_image(frame)
                    # Procesar el resultado del análisis según sea necesario
                    payload = {
                        'device': 'Raspberry Pi 3',
                        'camera_analysis': analysis_result
                    }
                    iot_client.publish(config['aws']['iot_topics']['data_publish'], payload)
                    print(f"Datos de análisis de cámara publicados: {payload}")
                time.sleep(1 / camera_module.frame_rate)
            else:
                time.sleep(1)
    except Exception as e:
        logging.error(f"Error en la transmisión de la cámara: {e}")

def handle_action(self, action):
    """
    Maneja las acciones seleccionadas en el menú táctil.
    """
    if action == 'adjust_valves':
        self.adjust_valves()
    elif action == 'calibrate_sensors':
        self.calibrate_sensors()
    elif action == 'start_camera':
        self.start_camera_analysis()
    elif action == 'stop_camera':
        self.stop_camera_analysis()
    elif action == 'view_status':
        self.view_status()
    else:
        messagebox.showerror("Error", f"Acción desconocida: {action}")

def start_camera_analysis(self):
    """
    Inicia el análisis de la cámara.
    """
    if self.camera_module:
        self.camera_module.streaming = True
        messagebox.showinfo("Cámara", "Análisis de cámara iniciado.")

def stop_camera_analysis(self):
    """
    Detiene el análisis de la cámara.
    """
    if self.camera_module:
        self.camera_module.streaming = False
        messagebox.showinfo("Cámara", "Análisis de cámara detenido.")

if __name__ == '__main__':
    main()
