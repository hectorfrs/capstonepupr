# main_pi1.py - Script principal para Raspberry Pi 1
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import sys
import os
import time
import json
import random
from datetime import datetime
from modules.logging_manager import LoggingManager
from modules.network_manager import NetworkManager
from modules.real_time_config import RealTimeConfigManager
from modules.config_manager import ConfigManager
from modules.mqtt_handler import MQTTHandler

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
    global logger
    # Configuración
    config_path = "/home/raspberry-1/capstonepupr/src/tst/configs/pi1_config.yaml"
    config_manager = ConfigManager(config_path)
    try:
        logging_manager = LoggingManager(config_manager)
        time.sleep(0.5)
    except Exception as e:
        logger.error(f"Error inicializando ConfigManager: {e}")
        raise
    
    # Inicializar logger básico para respaldo en caso de fallos
    logger = logging_manager.setup_logger("[MAIN PI-1]")
    time.sleep(0.5)
    try:
        logger.info("=" * 70)
        logger.info("Iniciando sistema de detección de materiales en Raspberry Pi 1")
        logger.info("=" * 70)

        # Cargar configuración dinámica
        logger.info("Iniciando monitoreo de configuración en tiempo real...")
        real_time_config = RealTimeConfigManager(config_manager)
        real_time_config.start_monitoring()
        config = real_time_config.get_config()

        # Configuración de red
        logger.info("Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        # Inicializa MQTTHandler
        mqtt_handler = MQTTHandler(config_manager)

        # Asigna el callback personalizado
        mqtt_handler.client.on_message = on_message_received

        # Conecta al broker MQTT y suscribe a tópicos
        mqtt_handler.connect_and_subscribe()

        # Publicación de prueba
        #mqtt_handler.publish("material/entrada", "Iniciando monitoreo")

        # Loop continuo para mensajes
        logger.info("Esperando mensajes MQTT de Raspberry 3...")
        mqtt_handler.client.loop_forever()

    except KeyboardInterrupt:
        logger.info("[PI-1] Apagando Monitoreo del Network...")
        network_manager.stop_monitoring()
        logger.info("[PI-1] Sistema apagado correctamente.")
    except Exception as e:
        logger.error(f"[PI-1] Error crítico en la ejecución: {e}")
    finally:
        logger.info("[PI-1] Finalizando ejecución del script.")
        if 'mqtt_handler' in globals() and mqtt_handler.is_connected():
            logger.info("[PI-1] Desconectando cliente MQTT...")
            mqtt_handler.disconnect()
            logger.info("[PI-1] Cliente MQTT desconectado.")

if __name__ == "__main__":
    main()
