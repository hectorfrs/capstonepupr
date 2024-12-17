# main.py - Script principal para controlar la simulación en Raspberry Pi 3
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import logging
import time
from utils.mqtt_handler import MQTTHandler
from utils.weight_sensor_simulation import simulate_weight_sensor
from utils.waste_type_simulation import simulate_waste_detection
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
        mqtt_config = config["mqtt"]
        mqtt_handler = MQTTHandler(
            client_id=mqtt_config["client_id"],
            broker_address=mqtt_config["broker_address"],
            port=mqtt_config["port"],
            keepalive=mqtt_config["keepalive"],
            topics=[mqtt_config["topics"]["entry"], mqtt_config["topics"]["detection"], mqtt_config["topics"]["action"]]
        )
        mqtt_handler.connect()

        # Configuración de simulación
        simulation_duration = config["simulation"]["duration"]
        communication_delay = config["communication"]["delay_to_pi1"]
        bucket_full_limit = 5000  # Umbral de peso para considerar el bucket lleno (en gramos)
        start_time = time.time()
        buckets_status = {"PET": 0, "HDPE": 0}

        # Iniciar la simulación de la cámara
        logging.info("[MAIN] Simulando cámara y detección de materiales...")
        simulate_camera_detection(mqtt_handler.client, mqtt_config["topics"]["entry"], [1, 3])

        # Bucle principal de la simulación
        while time.time() - start_time < simulation_duration:
            # Simular peso de los buckets
            weight_data = simulate_weight_sensor()
            buckets_status["PET"] += weight_data["PET"]
            buckets_status["HDPE"] += weight_data["HDPE"]

            # Revisar si los buckets están llenos
            if buckets_status["PET"] >= bucket_full_limit or buckets_status["HDPE"] >= bucket_full_limit:
                logging.info(f"[MAIN] Bucket lleno detectado. Estado actual: {buckets_status}")
                mqtt_handler.publish(
                    topic=mqtt_config["topics"]["entry"],
                    payload={"status": "simulation_ended", "buckets": buckets_status}
                )
                break

            # Publicar datos simulados de peso
            mqtt_handler.publish(
                topic=mqtt_config["topics"]["entry"],
                payload={"status": "material_detected", "weight": weight_data, "timestamp": time.time()}
            )

            # Simular detección de residuos y publicación
            waste_data = simulate_waste_detection()
            mqtt_handler.publish(
                topic=mqtt_config["topics"]["detection"],
                payload=waste_data
            )

            # Log y delay de comunicación
            logging.info(f"[MAIN] Estado actual de los buckets: {buckets_status}")
            logging.info(f"[MAIN] Esperando {communication_delay} segundos para enviar los datos...")
            time.sleep(communication_delay)

        logging.info("[MAIN] Simulación completada. Finalizando script.")

    except Exception as e:
        logging.error(f"[MAIN] Error crítico en la ejecución: {e}")
    finally:
        logging.info("[MAIN] Finalizando ejecución del script.")

if __name__ == "__main__":
    main()
