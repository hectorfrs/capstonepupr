# main_pi2.py - Script principal para Raspberry Pi 2
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import time
import json
import random
from modules.logging_manager import setup_logger
from modules.network_manager import NetworkManager
from modules.real_time_config import RealTimeConfigManager
from modules.config_manager import ConfigManager
from modules.mqtt_handler import MQTTHandler
from modules.relay_controller import RelayController

# Función para calcular el delay basado en distancia y velocidad del conveyor
def calculate_delay(distance, speed):
    """
    Calcula el tiempo de delay basado en la distancia y velocidad.
    :param distance: Distancia en pulgadas.
    :param speed: Velocidad del conveyor en pulgadas por segundo.
    :return: Tiempo de delay en segundos.
    """
    if speed <= 0:
        raise ValueError("La velocidad debe ser mayor que cero.")
    return round(distance / speed, 2)

def on_message_received(client, userdata, msg):
    """
    Callback para procesar mensajes MQTT y activar relay.
    """
    try:
        raw_payload = msg.payload.decode()
        logger.info(f"[MQTT] Mensaje recibido en '{msg.topic}': {raw_payload}")

        if not raw_payload.strip():
            logger.warning("[PI2] Mensaje recibido está vacío.")
            return

        try:
            payload = json.loads(raw_payload)
            logger.info(f"[PI2] Mensaje recibido | Tópico: {msg.topic} | Payload: {payload}")
        except json.JSONDecodeError as e:
            logger.error(f"[PI2] Error decodificando JSON: {e}")
            return

        material_type = payload.get("tipo", "Unknown")
        action_time = payload.get("tiempo", 0)

        logger.info(f"[PI2] Material: {material_type} | Tiempo: {action_time}s")

        if material_type in ["PET", "HDPE"]:
            relay_index = 0 if material_type == "PET" else 1
            relay_controller.activate_relay(relay_index, action_time)
            logger.info(f"[PI2] Activado Relay {relay_index} por {action_time}s para {material_type}.")
        else:
            logger.warning(f"[PI2] Material desconocido: {material_type}")

    except Exception as e:
        logger.error(f"[PI2] Error procesando mensaje: {e}")

def main():
    global relay_controller
    try:
        # Configuración
        config_path = "/home/raspberry-2/capstonepupr/src/tst/configs/pi2_config.yaml"
        config_manager = ConfigManager(config_path)
        config = config_manager.config

        # Configurar logger global
        global logger
        logging_manager = LoggingManager(config_manager)
        logger = setup_logger("[MAIN PI2]", config_manager.get("logging", {}))

        logger.info("=" * 70)
        logger.info("[PI2] Iniciando sistema de control de Relay en Raspberry Pi 2")
        logger.info("=" * 70)

        # Configuración de red
        logger.info("[PI2] [NET] Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        # Cargar configuración dinámica
        real_time_config = RealTimeConfigManager(config_path)
        real_time_config.start_monitoring()
        config = real_time_config.get_config()

        # Obtener velocidad del conveyor y distancias configuradas
        conveyor_speed = config["system"].get("conveyor_speed", 100)
        distances = config.get("delays", {})

        # Calcular delays
        delay_sensor_to_valve_1 = calculate_delay(distances["sensor_to_valve_1"], conveyor_speed)
        delay_sensor_to_valve_2 = calculate_delay(distances["sensor_to_valve_2"], conveyor_speed)

        logging.info(f"[PI2] Delay sensor a válvula 1: {delay_sensor_to_valve_1} segundos")
        logging.info(f"[PI2] Delay sensor a válvula 2: {delay_sensor_to_valve_2} segundos")

        # Configurar MQTT
        logger.info("[PI2] [MQTT] Configurando cliente MQTT...")
        mqtt_config = config.get("mqtt", {})
        global mqtt_handler
        mqtt_handler = MQTTHandler(mqtt_config)
        mqtt_handler.client.on_message = on_message_received

        mqtt_handler.connect()
        #mqtt_handler.subscribe("material/entrada")
        mqtt_client.subscribe(mqtt_config["topics"]["entry"])

        # Configuración de relay
        logger.info("[PI2] Configurando controlador de relay...")
        relay_config = config.get("mux", {}).get("relays", [])
        relay_controller = RelayController(relay_config)

        logger.info("[PI2] Esperando señales MQTT para control de relay...")
        mqtt_handler.forever_loop()

    except KeyboardInterrupt:
        logger.info("[PI2] Apagando Monitoreo del Network...")
        network_manager.stop_monitoring()
        logger.info("[PI2] Sistema apagado correctamente.")
    except Exception as e:
        logger.error(f"[PI2] Error crítico en la ejecución: {e}")
    finally:
        logger.info("[PI2] Finalizando ejecución del script.")
        if 'mqtt_handler' in globals() and mqtt_handler.is_connected():
            logger.info("[PI2] Desconectando cliente MQTT...")
            mqtt_handler.disconnect()
            logger.info("[PI2] Cliente MQTT desconectado.")

if __name__ == "__main__":
    main()
