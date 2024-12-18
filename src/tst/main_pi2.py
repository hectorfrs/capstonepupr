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

def on_message_received(client, userdata, msg):
    """
    Callback para procesar mensajes MQTT y activar relés.
    """
    try:
        raw_payload = msg.payload.decode()
        logger.info(f"[MQTT] Mensaje recibido en '{msg.topic}': {raw_payload}")

        if not raw_payload.strip():
            logger.warning("[MAIN] Mensaje recibido está vacío.")
            return

        try:
            payload = json.loads(raw_payload)
            logger.info(f"[MAIN] Mensaje recibido | Tópico: {msg.topic} | Payload: {payload}")
        except json.JSONDecodeError as e:
            logger.error(f"[MAIN] Error decodificando JSON: {e}")
            return

        material_type = payload.get("tipo", "Unknown")
        action_time = payload.get("tiempo", 0)

        logger.info(f"[MAIN] Material: {material_type} | Tiempo: {action_time}s")

        if material_type in ["PET", "HDPE"]:
            relay_index = 0 if material_type == "PET" else 1
            relay_controller.activate_relay(relay_index, action_time)
            logger.info(f"[MAIN] Activado Relay {relay_index} por {action_time}s para {material_type}.")
        else:
            logger.warning(f"[MAIN] Material desconocido: {material_type}")

    except Exception as e:
        logger.error(f"[MAIN] Error procesando mensaje: {e}")

def main():
    try:
        # Configuración
        config_path = "/home/raspberry-2/capstonepupr/src/tst/configs/pi2_config.yaml"
        config_manager = ConfigManager(config_path)

        # Configurar logger global
        global logger
        logger = setup_logger("[MAIN PI2]", config_manager.get("logging", {}))

        logger.info("=" * 70)
        logger.info("[MAIN] Iniciando sistema de control de Relay en Raspberry Pi 2")
        logger.info("=" * 70)

        # Cargar configuración dinámica
        real_time_config = RealTimeConfigManager(config_path)
        real_time_config.start_monitoring()
        config = real_time_config.get_config()

        # Configuración de red
        logger.info("[MAIN] [NET] Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        # Configurar MQTT
        logger.info("[MAIN] [MQTT] Configurando cliente MQTT...")
        mqtt_config = config.get("mqtt", {})
        global mqtt_handler
        mqtt_handler = MQTTHandler(mqtt_config)
        mqtt_handler.client.on_message = on_message_received

        mqtt_handler.connect()
        mqtt_handler.subscribe("material/entrada")

        # Configuración de relés
        logger.info("[MAIN] Configurando controlador de relés...")
        relay_config = config.get("mux", {}).get("relays", [])
        global relay_controller
        relay_controller = RelayController(relay_config)

        logger.info("[MAIN] Esperando señales MQTT para control de relés...")
        mqtt_handler.forever_loop()

    except KeyboardInterrupt:
        logger.info("[MAIN] Apagando Monitoreo del Network...")
        network_manager.stop_monitoring()
        logger.info("[MAIN] Sistema apagado correctamente.")
    except Exception as e:
        logger.error(f"[MAIN] Error crítico en la ejecución: {e}")
    finally:
        logger.info("[MAIN] Finalizando ejecución del script.")
        if 'mqtt_handler' in globals() and mqtt_handler.is_connected():
            logger.info("[MAIN] Desconectando cliente MQTT...")
            mqtt_handler.disconnect()
            logger.info("[MAIN] Cliente MQTT desconectado.")

if __name__ == "__main__":
    main()
