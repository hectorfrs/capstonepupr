# main_pi3.py - Script principal para Raspberry Pi 3
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import time
import json
import random
import uuid
from modules.logging_manager import LoggingManager
from modules.network_manager import NetworkManager
from modules.real_time_config import RealTimeConfigManager
from modules.config_manager import ConfigManager
from modules.mqtt_handler import MQTTHandler
from raspberry_pi.pi3.utils.camera_simulation import simulate_camera_detection

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

def detect_material(mqtt_handler, material):
    """
    Simula la detección de un material y publica el evento con un ID único.
    """
    try:
        # Generar un ID único para el evento
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # Log del evento detectado
        logger.info(f"[RPI3] Material detectado: {material} | ID Evento: {event_id} | Timestamp: {timestamp}")

        # Crear payload del evento
        payload = {
            "id": event_id,
            "timestamp": timestamp,
            "material": material
        }

        # Publicar el evento en MQTT
        mqtt_handler.publish("material/entrada", payload)
        logger.info(f"[RPI3] Evento publicado en MQTT: {payload}")

    except Exception as e:
        logger.error(f"[RPI3] Error detectando material: {e}")

def main():
    global logger
    # Configuración
    config_path = "/home/raspberry-3/capstonepupr/src/tst/configs/pi3_config.yaml"
    try:
        config_manager = ConfigManager(config_path)
        time.sleep(0.5)
        logging_manager = LoggingManager(config_manager)
        time.sleep(0.5)
    except Exception as e:
        logger.error(f"Error inicializando ConfigManager: {e}")
        raise
    
    # Inicializar logger básico para respaldo en caso de fallos
    logger = logging_manager.setup_logger("[MAIN PI-3]")
    try:
        logger.info("=" * 70)
        logger.info("Iniciando sistema de simulación en Raspberry Pi 3")
        logger.info("=" * 70)

        # Cargar configuración dinámica
        logger.info("Iniciando monitoreo de configuración en tiempo real...")
        real_time_config = RealTimeConfigManager(config_manager)
        real_time_config.start_monitoring()
        config = real_time_config.get_config()
        time.sleep(1)

        # Configuración de red
        logger.info("Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()
        time.sleep(1)

        # Inicializa MQTTHandler
        mqtt_handler = MQTTHandler(config_manager)

        # Asigna el callback personalizado
        mqtt_handler.client.on_message = on_message_received

        # Conecta al broker MQTT y suscribe a tópicos
        mqtt_handler.connect_and_subscribe()

        # Publicación de prueba
        mqtt_handler.publish("valvula/estado", "Iniciando monitoreo")

        # Loop continuo para mensajes
        logger.info("Esperando mensajes MQTT...")
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

if __name__ == "__main__":
    main()
