# main.py - Script principal para controlar la simulación en Raspberry Pi 3
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import logging
import time
import yaml
from utils.mqtt_handler import MQTTHandler
from utils.weight_sensor import WeightSensor
from utils.waste_type import WasteTypeDetector
from utils.real_time_config import RealTimeConfigManager
from utils.network_manager import NetworkManager
from utils.camera_simulation import simulate_camera_detection

# Configurar logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

def main():
    """
    Script principal para la simulación de detección de materiales en Raspberry Pi 3.
    """
    try:
        logging.info("=" * 70)
        logging.info("[MAIN] Iniciando simulación en Raspberry Pi 3")
        logging.info("=" * 70)

        # Cargar configuración
        config_path = "/home/raspberry-3/capstonepupr/src/pi3/config/config.yaml"
        config_manager = RealTimeConfigManager(config_path)
        config_manager.start_monitoring()
        config = config_manager.get_config()

        # Inicializar monitoreo de red
        logging.info("[MAIN] Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        # Configuración de MQTT
        logging.info("[MAIN] [MQTT] Configurando cliente MQTT...")
        mqtt_config = config["mqtt"]
        mqtt_handler = MQTTHandler(mqtt_config)
        mqtt_handler.client.on_message = on_message_received

        # Configuración de simulación
        simulation_duration = config["simulation"]["duration"]
        communication_delay = config["communication"]["delay_to_pi1"]
        bucket_full_limit = 5000  # Umbral de peso para considerar el bucket lleno (en gramos)
        start_time = time.time()
        buckets_status = {"PET": 0, "HDPE": 0}

        # Iniciar la simulación de la cámara
        logging.info("[MAIN] Simulando cámara y detección de materiales...")
        # Simulación de la cámara y detección de materiales
        simulate_camera_detection(
            mqtt_handler=mqtt_handler, 
            topic=mqtt_config["topics"]["entry"],
            delay_range=[1, 3]  # Delay entre 1 y 3 segundos
        )

        # Configuración inicial de los buckets
        buckets = {
            "Bucket 1 (PET)": 0,   # Peso inicial en gramos
            "Bucket 2 (HDPE)": 0   # Peso inicial en gramos
        }

        # Inicializar el simulador de sensores de peso
        weight_sensor = WeightSensor(buckets)

        # Bucle principal de la simulación
        while time.time() - start_time < simulation_duration:
            # Simular peso de los buckets
            weight_sensor.simulate_weight()
            weight_data = weight_sensor.get_weights()
            logging.info(f"[MAIN] Pesos actuales: {weight_data}")

            # Revisar si los buckets están llenos
            if weight_data["Bucket 1 (PET)"] >= bucket_full_limit or weight_data["Bucket 2 (HDPE)"] >= bucket_full_limit:
                logging.info(f"[MAIN] Bucket lleno detectado. Estado actual: {weight_data}")
                mqtt_handler.publish(
                    topic=mqtt_config["topics"]["entry"],
                    payload={"status": "simulation_ended", "buckets": weight_data}
                )
                break

            # Publicar datos simulados de peso
            mqtt_handler.publish(
                topic=mqtt_config["topics"]["status"],
                payload={"status": "material_detected", "weight": weight_data, "timestamp": time.time()}
            )

            # Simular detección de residuos y publicación
            waste_data = WasteTypeDetector().generate_waste_data()
            mqtt_handler.publish(
                topic=mqtt_config["topics"]["detection"],
                payload=waste_data
            )

            # Log y delay de comunicación
            logging.info(f"[MAIN] Estado actual de los buckets: {weight_data}")
            logging.info(f"[MAIN] Esperando {communication_delay} segundos para enviar los datos...")
            time.sleep(communication_delay)


        logging.info("[MAIN] Simulación completada. Finalizando script.")

    except KeyboardInterrupt:
        logging.info("[MAIN] Apagando Monitoreo del Network...")
        network_manager.stop_monitoring()
        logging.info("[MAIN] Sistema apagado correctamente.")
    except Exception as e:
        logging.error(f"[MAIN] Error crítico en la ejecución: {e}")
    finally:
        logging.info("[MAIN] Finalizando ejecución del script.")
        mqtt_handler.disconnect()
        logging.info("[MAIN] Cliente MQTT desconectado.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error crítico en la ejecución: {e}")
