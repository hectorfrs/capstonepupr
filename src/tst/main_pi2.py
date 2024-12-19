# main_pi2.py - Script principal para Raspberry Pi 2
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import json
import logging
import time
import random
from modules.config_manager import ConfigManager
from modules.real_time_config import RealTimeConfigManager
from modules.network_manager import NetworkManager
from modules.mqtt_handler import MQTTHandler
from modules.logging_manager import LoggingManager
from raspberry_pi.pi2.sim.relay_controller import RelayController # Cambiar a la línea de abajo para usar el controlador real
#from raspberry_pi.pi2.lib.relay_controller import RelayController # Cambiar a la línea de arriba para usar el controlador simulado

# Configuración inicial del logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MAIN PI-2")

# Función para calcular delay basado en la distancia y velocidad del conveyor
def calculate_delay(distance, conveyor_speed):
    return round(distance / conveyor_speed, 2)

def on_message_received(client, userdata, msg, relay_controller):
    """
    Procesa mensajes MQTT en Raspberry 2.
    """
    try:
        payload = json.loads(msg.payload.decode())

        # Extraer datos del mensaje
        event_id = payload.get("id", "Sin ID")
        timestamp = payload.get("timestamp", "Sin Timestamp")
        material = payload.get("material", "Desconocido")

        # Log del evento recibido
        logger.info(f"[PI2] Evento recibido | ID: {event_id} | Material: {material} | Timestamp: {timestamp}")

        # Obtener configuración dinámica de tiempos
        activation_time_min = config["mux"].get("activation_time_min", 0.5)
        activation_time_max = config["mux"].get("activation_time_max", 3.0)
        activation_time = round(random.uniform(activation_time_min, activation_time_max), 2)

        # Activar el relay según el material detectado
        if material in ["PET", "HDPE"]:
            relay_index = 0 if material == "PET" else 1
            relay_controller.activate_relay(relay_index, activation_time)
            logger.info(f"[PI2] Relay {relay_index} activado para {material} por {activation_time} segundos. ID Evento: {event_id}")
        else:
            logger.warning(f"[PI2] Material desconocido: {material}. ID Evento: {event_id}")

    except json.JSONDecodeError as e:
        logger.error(f"[PI2] Error decodificando JSON: {e}")
    except Exception as e:
        logger.error(f"[PI2] Error procesando mensaje: {e}")

def main():
    try:
        logger.info("=" * 70)
        logger.info("Iniciando sistema de control de Relay en Raspberry Pi 2")
        logger.info("=" * 70)

        # Cargar configuración dinámica
        logger.info("Iniciando monitoreo de configuración en tiempo real...")
        config_manager = ConfigManager("/home/raspberry-2/capstonepupr/src/tst/configs/pi2_config.yaml")

        # Limpiar caché antes de iniciar
        logger.info("Limpiando caché de configuraciones...")
        config_manager.clear_cache()

        real_time_config = RealTimeConfigManager(config_manager)
        real_time_config.start_monitoring()
        global config
        config = real_time_config.get_config()

        # Configuración de red
        logger.info("Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        # Obtener velocidad del conveyor y distancias configuradas
        conveyor_speed = config["system"].get("conveyor_speed", 100)
        distances = config.get("delays", {})

        # Calcular delays
        delay_sensor_to_valve_1 = calculate_delay(distances.get("sensor_to_valve_1", 0), conveyor_speed)
        delay_sensor_to_valve_2 = calculate_delay(distances.get("sensor_to_valve_2", 0), conveyor_speed)

        logger.info(f"[PI2] Delay sensor a válvula 1: {delay_sensor_to_valve_1} segundos")
        logger.info(f"[PI2] Delay sensor a válvula 2: {delay_sensor_to_valve_2} segundos")

        # Configuración de relay
        logger.info("[PI2] Configurando controlador de relay...")
        relay_controller = RelayController(config["mux"]["relays"])

        # Inicializa MQTTHandler
        mqtt_handler = MQTTHandler(config_manager)
        mqtt_handler.client.on_message = lambda client, userdata, msg: on_message_received(client, userdata, msg, relay_controller)
        mqtt_handler.connect()

        logger.info("[PI2] Sistema operativo en espera de mensajes...")

        # Inicia el loop de MQTT
        mqtt_handler.forever_loop()

    except Exception as e:
        logger.error(f"[PI2] Error crítico en la ejecución: {e}")

    finally:
        logger.info("[PI2] Apagando Monitoreo del Network...")
        network_manager.stop_monitoring()
        logger.info("[PI2] Sistema apagado correctamente.")
        logger.info("[PI2] Finalizando ejecución del script.")

if __name__ == "__main__":
    main()
