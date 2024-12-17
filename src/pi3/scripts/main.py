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
        logging.info("=" * 80)
        logging.info("[MAIN] Iniciando Sistema de Control de Materiales.")
        logging.info("=" * 80)

        # Cargar configuración en tiempo real
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
            topics=[mqtt_config["topics"]["action"], mqtt_config["topics"]["status"]]
        )
        mqtt_handler.connect()

        # Configuración de simulación
        simulation_duration = config["simulation"]["duration"]
        communication_delay = config["communication"]["delay_to_pi1"]
        start_time = time.time()

        # Simular la cámara y enviar datos a Raspberry Pi 1
        logging.info("[MAIN] Iniciando simulación de la cámara...")
        simulate_camera_detection(mqtt_handler.client, mqtt_config["topics"]["entry"], [1, 3])

        logging.info(f"[MAIN] Iniciando simulación por {simulation_duration} segundos...")
        while time.time() - start_time < simulation_duration:
            # Simular datos de peso
            weight_data = simulate_weight_sensor()
            logging.info(f"[MAIN] Peso simulado: {weight_data} g")

            # Publicar mensaje de entrada de material
            mqtt_handler.publish(
                topic=mqtt_config["topics"]["entry"],
                payload={
                    "status": "material_detected",
                    "weight": weight_data,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            )

            # Simular detección de residuos y publicarlos
            waste_data = simulate_waste_detection()
            mqtt_handler.publish(
                topic=mqtt_config["topics"]["detection"],
                payload=waste_data
            )
            logging.info(f"[MAIN] Datos de detección publicados: {waste_data}")

            # Simular delay en la comunicación con Raspberry Pi 1
            logging.info(f"[MAIN] Esperando {communication_delay} segundos para enviar datos...")
            time.sleep(communication_delay)

        logging.info("[MAIN] Simulación completada. Finalizando script.")

    except Exception as e:
        logging.error(f"[MAIN] Error crítico en la ejecución: {e}")
    finally:
        logging.info("[MAIN] Finalizando ejecución del script.")

if __name__ == "__main__":
    main()
