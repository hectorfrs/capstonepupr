# main_pi1.py - Script principal para Raspberry Pi 1
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import sys
import os
import time
import json
import random
import logging
from datetime import datetime
from modules.network_manager import NetworkManager
from modules.real_time_config import RealTimeConfigManager
from modules.config_manager import ConfigManager
from modules.mqtt_handler import MQTTHandler

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(message)s",
    )
    return logging.getLogger("MAIN PI-1")

def calculate_delay(distance, conveyor_speed):
    return round(distance / conveyor_speed, 2)

def on_message_received(client, userdata, msg):
    """
    Procesa mensajes MQTT en Raspberry 1.
    """
    try:
        payload = json.loads(msg.payload.decode())

        # Extraer datos del mensaje
        event_id = payload.get("id", "Sin ID")
        timestamp = payload.get("timestamp", "Sin Timestamp")
        material = payload.get("material", "Desconocido")

        # Log del evento recibido
        logger.info(f"[RPI1] Evento recibido | ID: {event_id} | Material: {material} | Timestamp: {timestamp}")

        # Realizar acciones adicionales si aplica
        # Ejemplo: validar el material
        if material not in ["PET", "HDPE"]:
            logger.warning(f"[RPI1] Material desconocido: {material}. ID Evento: {event_id}")
        else:
            logger.info(f"[RPI1] Material válido: {material}. ID Evento: {event_id}")

    except json.JSONDecodeError as e:
        logger.error(f"[RPI1] Error decodificando JSON: {e}")
    except Exception as e:
        logger.error(f"[RPI1] Error procesando mensaje: {e}")


def main():
    logger = setup_logger()
    network_manager = None  # Inicialización para evitar errores de referencia
    mqtt_handler = None     # Inicialización para evitar errores de referencia

    try:
        logger.info("=" * 70)
        logger.info("Iniciando sistema de detección de materiales en Raspberry Pi 1")
        logger.info("=" * 70)

        # Configuración del sistema
        config_path = "/home/raspberry-1/capstonepupr/src/tst/configs/pi1_config.yaml"
        config_manager = ConfigManager(config_path)
        
        # Limpiar caché antes de iniciar
        logger.info("Limpiando caché de configuraciones...")
        config_manager.clear_cache()
        time.sleep(0.5)

        real_time_config = RealTimeConfigManager(config_manager)
        real_time_config.start_monitoring()

        # Obtener configuración
        config = real_time_config.get_config()

        # Configuración de red
        logger.info("Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        # Inicializa MQTTHandler
        mqtt_handler = MQTTHandler(config_manager)
        mqtt_handler.client.on_message = on_message_received
        mqtt_handler.connect_and_subscribe()
        logger.info("Esperando mensajes MQTT de Raspberry 3...")
        mqtt_handler.client.loop_forever()

        # Cálculo de delay y simulación de detección
        distance_to_sensor = config["system"].get("distance_to_sensor", 24)  # en pulgadas
        conveyor_speed = config["system"].get("conveyor_speed", 100)  # en pulgadas por segundo
        evaluation_time_min = 0.1
        evaluation_time_max = 1.0

        while True:
            # Simula el tiempo de llegada del material al sensor
            delay_to_sensor = calculate_delay(distance_to_sensor, conveyor_speed)
            logger.info(f"[PI-1] Tiempo estimado para llegada al sensor: {delay_to_sensor} segundos")
            time.sleep(delay_to_sensor)

            # Simula la evaluación del material
            evaluation_time = round(random.uniform(evaluation_time_min, evaluation_time_max), 2)
            logger.info(f"[PI-1] Evaluando material durante {evaluation_time} segundos")
            time.sleep(evaluation_time)

            # Publica el material evaluado a Raspberry Pi 2
            event_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            material = random.choice(["PET", "HDPE", "UNKNOWN"])

            payload = {
                "id": event_id,
                "timestamp": timestamp,
                "material": material,
            }

            logger.info(f"[PI-1] Material evaluado: {material} | ID Evento: {event_id}")
            mqtt_handler.publish("material/entrada", payload)
            logger.info(f"[PI-1] Evento publicado en MQTT: {payload}")

    except KeyboardInterrupt:
        logger.info("Interrupción detectada. Apagando sistema...")
        if network_manager:
            logger.info("Apagando Monitoreo del Network...")
            network_manager.stop_monitoring()
            logger.info("Sistema apagado correctamente.")        
        
    except Exception as e:
        logger.error(f"Error crítico en la ejecución: {e}")
    finally:
        if network_manager:
            network_manager.stop_monitoring()
        if mqtt_handler.is_connected():
            logger.info("Desconectando cliente MQTT...")
            mqtt_handler.disconnect()
            logger.info("Cliente MQTT desconectado.")
        if real_time_config():
            logger.info("Deteniendo monitoreo de configuración...")
            real_time_config.stop_monitoring()
            logger.info("Monitoreo de configuración detenido.")
        logger.info("Proceso finalizado.")
        sys.exit(0)

if __name__ == "__main__":
    main()

