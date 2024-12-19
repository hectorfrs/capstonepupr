# main_pi3.py - Script principal para Raspberry Pi 3
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import time
import json
import random
import uuid
import logging
from datetime import datetime
from modules.network_manager import NetworkManager
from modules.real_time_config import RealTimeConfigManager
from modules.config_manager import ConfigManager
from modules.mqtt_handler import MQTTHandler
from raspberry_pi.pi3.utils.camera_simulation import simulate_camera_detection

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(message)s",
    )
    return logging.getLogger("MAIN PI-3")

def on_message_received(client, userdata, msg):
    """
    Callback para procesar mensajes MQTT.
    """
    try:
        raw_payload = msg.payload.decode()
        logger.info(f"[MQTT] Mensaje recibido en '{msg.topic}': {raw_payload}")

        if not raw_payload.strip():
            logger.warning("[PI-3] Mensaje recibido está vacío.")
            return

        try:
            payload = json.loads(raw_payload)
            logger.info(f"[PI-3] Mensaje recibido | Tópico: {msg.topic} | Payload: {payload}")
        except json.JSONDecodeError as e:
            logger.error(f"[PI-3] Error decodificando JSON: {e}")
            return

        status = payload.get("status", "Unknown")
        buckets = payload.get("buckets", {})

        logger.info(f"[PI-3] Estado recibido: {status} | Buckets: {buckets}")

    except Exception as e:
        logger.error(f"[PI-3] Error procesando mensaje: {e}")

def detect_and_publish(mqtt_handler, material):
    """
    Detecta el material, genera un evento ID y publica el mensaje en el tópico correspondiente.
    """
    event_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    payload = {
        "id": event_id,
        "timestamp": timestamp,
        "material": material
    }

    logger.info(f"[RPI3] Material detectado: {material} | ID Evento: {event_id}")
    mqtt_handler.publish("material/deteccion", payload)
    logger.info(f"[RPI3] Evento publicado en MQTT: {payload}")

def handle_processed_material(client, userdata, msg):
    """
    Maneja el material procesado por los otros Raspberry Pis y registra el pesaje del material.
    """
    payload = json.loads(msg.payload.decode())
    event_id = payload.get("id", "Sin ID")
    material = payload.get("material", "Desconocido")
    logger.info(f"[RPI3] Material procesado recibido | ID Evento: {event_id} | Material: {material}")

    weight = random.uniform(1, 5)  # Simular el pesaje
    weighing_payload = {
        "id": event_id,
        "material": material,
        "weight": round(weight, 2)
    }

    mqtt_handler.publish("material/pesaje", weighing_payload)
    logger.info(f"[RPI3] Pesaje registrado: {weighing_payload}")

def main():
    logger = setup_logger()
    network_manager = None
    mqtt_handler = None
    network_manager = None  # Inicialización para evitar errores de referencia
    try:
        logger.info("=" * 70)
        logger.info("Iniciando sistema de simulación en Raspberry Pi 3")
        logger.info("=" * 70)

        # Configuración del sistema
        config_path = "/home/raspberry-3/capstonepupr/src/tst/configs/pi3_config.yaml"
        config_manager = ConfigManager(config_path)
        config_manager.clear_cache()

        real_time_config = RealTimeConfigManager(config_manager)
        real_time_config.start_monitoring()
        config = real_time_config.get_config()

        # Configuración de red
        logger.info("Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()
        time.sleep(1)

        # Inicializar MQTTHandler
        mqtt_handler = MQTTHandler(config_manager)

        # Publicar un mensaje inicial
        #mqtt_handler.publish("material/entrada", {"message": "Sistema iniciado en Raspberry Pi 3"})

        # Simular detección de materiales
        materials = ["PET", "HDPE", "UNKNOWN"]
        for material in materials:
            detect_material(mqtt_handler, material)

        # Mantener el loop MQTT
        logger.info("[PI-3] Esperando mensajes MQTT...")
        mqtt_handler.client.loop_forever()

        # Configuración de simulación
        simulation_duration = config.get("simulation", {}).get("duration", 60)
        communication_delay = config.get("communication", {}).get("delay_to_pi1", 5)
        bucket_full_limit = 5000  # Umbral de peso para considerar el bucket lleno (en gramos)

        logger.info("[PI-3] Configurando simulación de cámara y detección de materiales...")

        # Simulación de la cámara y detección de materiales
        simulate_camera_detection(
            mqtt_handler=mqtt_handler, 
            topic=mqtt_config.get("topics", {}).get("entry", "raspberry-3/entry"),
            delay_range=[1, 3]  # Delay entre 1 y 3 segundos
        )

        # Configuración inicial de los buckets
        buckets = {
            "Bucket 1 (PET)": 0,   # Peso inicial en gramos
            "Bucket 2 (HDPE)": 0   # Peso inicial en gramos
        }

        # Inicializar el simulador de sensores de peso
        weight_sensor = WeightSensor(buckets)

        start_time = time.time()

        # Bucle principal de la simulación
        while time.time() - start_time < simulation_duration:
            # Simular peso de los buckets
            weight_sensor.simulate_weight()
            weight_data = weight_sensor.get_weights()
            logger.info(f"[PI-3] Pesos actuales: {weight_data}")

            # Revisar si los buckets están llenos
            if weight_data["Bucket 1 (PET)"] >= bucket_full_limit or weight_data["Bucket 2 (HDPE)"] >= bucket_full_limit:
                logger.info(f"[PI-3] Bucket lleno detectado. Estado actual: {weight_data}")
                mqtt_handler.publish(
                    topic=mqtt_config.get("topics", {}).get("status", "raspberry-3/status"),
                    payload={"status": "simulation_ended", "buckets": weight_data, "id": str(uuid.uuid4())}
                )
                break

            # Publicar datos simulados de peso
            mqtt_handler.publish(
                topic=mqtt_config.get("topics", {}).get("status", "raspberry-3/status"),
                payload={"status": "material_detected", "weight": weight_data, "timestamp": time.time(), "id": str(uuid.uuid4())}
            )

            time.sleep(communication_delay)

        logger.info("[PI-3] Simulación completada. Finalizando script.")

    except KeyboardInterrupt:
        logger.info("[PI-3] Apagando Monitoreo del Network...")
        network_manager.stop_monitoring()
        logger.info("[PI-3] Sistema apagado correctamente.")
    except Exception as e:
        logger.error(f"[PI-3] Error crítico en la ejecución: {e}")
    finally:
        logger.info("[PI-3] Finalizando ejecución del script.")
        if 'mqtt_handler' in globals() and mqtt_handler.is_connected():
            logger.info("[PI-3] Desconectando cliente MQTT...")
            mqtt_handler.disconnect()
            logger.info("[PI-3] Cliente MQTT desconectado.")
        if 'logging_manager' in globals():
            logging_manager.close_handlers()
            logger.info("[PI-3] Handlers de logging cerrados.")
        if 'real_time_config' in globals():
            real_time_config.stop_monitoring()
            logger.info("[PI-3] Monitoreo de configuración detenido.")
        if 'network_manager' in globals():
            network_manager.stop_monitoring()
            logger.info("[PI-3] Monitoreo de red detenido.")
        logger.info("[PI-3] Proceso finalizado.")

if __name__ == "__main__":
    main()
