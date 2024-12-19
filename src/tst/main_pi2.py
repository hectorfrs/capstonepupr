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

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(message)s",
    )
    return logging.getLogger("MAIN PI-2")

# Función para calcular delay basado en la distancia y velocidad del conveyor
def calculate_delay(distance, conveyor_speed):
    """
    Calcula el tiempo de delay basado en la distancia al relay y la velocidad del conveyor.

    :param distance: Distancia en metros.
    :param conveyor_speed: Velocidad del conveyor en metros por segundo.
    :return: Tiempo de delay en segundos.
    """
    return round(distance / conveyor_speed, 2)

def activate_relays(client, userdata, msg, relay_controller):
    payload = json.loads(msg.payload.decode())
    event_id = payload.get("id", "Sin ID")
    category = payload.get("category", "Desconocido")
    activation_time = payload.get("activation_time", 1.0)

    relay_config = next((relay for relay in config["mux"]["relays"] if relay["category"] == category), None)
    if relay_config:
        relay_index = relay_config["mux_channel"]
        relay_controller.activate_relay(relay_index, activation_time)
        logger.info(f"[PI2] Relay {relay_index} activado para categoría {category} por {activation_time} segundos.")
        
        # Publicar mensaje de material procesado
        processed_payload = {"id": event_id, "material": category}
        mqtt_handler.publish("material/procesado", processed_payload)
    else:
        logger.warning(f"[PI2] Categoría no encontrada: {category}. ID Evento: {event_id}")

def on_message_received(client, userdata, msg, relay_controller):
    try:
        payload = json.loads(msg.payload.decode())

        event_id = payload.get("id", "Sin ID")
        timestamp = payload.get("timestamp", "Sin Timestamp")
        material = payload.get("material", "Desconocido")

        logger.info(f"[PI2] Evento recibido | ID: {event_id} | Material: {material} | Timestamp: {timestamp}")

        activation_time_min = config["mux"].get("activation_time_min", 0.5)
        activation_time_max = config["mux"].get("activation_time_max", 3.0)
        activation_time = round(random.uniform(activation_time_min, activation_time_max), 2)

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
    logger = setup_logger()
    network_manager = None
    mqtt_handler = None
    try:
        logger.info("=" * 70)
        logger.info("Iniciando sistema de control de Relay en Raspberry Pi 2")
        logger.info("=" * 70)

        config_path = "/home/raspberry-2/capstonepupr/src/tst/configs/pi2_config.yaml"
        config_manager = ConfigManager(config_path)

        logger.info("Limpiando caché de configuraciones...")
        config_manager.clear_cache()

        real_time_config = RealTimeConfigManager(config_manager)
        real_time_config.start_monitoring()
        global config
        config = real_time_config.get_config()

        logger.info("Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        conveyor_speed = config["system"].get("conveyor_speed", 100)
        distances = config.get("delays", {})

        delay_sensor_to_valve_1 = calculate_delay(distances.get("sensor_to_valve_1", 0), conveyor_speed)
        delay_sensor_to_valve_2 = calculate_delay(distances.get("sensor_to_valve_2", 0), conveyor_speed)

        logger.info(f"[PI2] Delay sensor a válvula 1: {delay_sensor_to_valve_1} segundos")
        logger.info(f"[PI2] Delay sensor a válvula 2: {delay_sensor_to_valve_2} segundos")

        logger.info("[PI2] Configurando controlador de relay...")
        relay_controller = RelayController(config["mux"]["relays"])

        # Inicializa MQTTHandler
        mqtt_handler = MQTTHandler(config_manager)
        mqtt_handler.client.on_message = lambda client, userdata, msg: on_message_received(client, userdata, msg, relay_controller)
        mqtt_handler.connect_and_subscribe()
        logger.info("Esperando mensajes MQTT de Raspberry 1...")
        mqtt_handler.client.loop_forever()

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
        if mqtt_handler():
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
