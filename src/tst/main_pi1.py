# main_pi1.py - Script principal para Raspberry Pi 1
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import time
import json
import random  # Importar random
from modules.logging_manager import setup_logger
from modules.network_manager import NetworkManager
from modules.real_time_config import RealTimeConfigManager
from modules.config_manager import ConfigManager
from modules.mqtt_handler import MQTTHandler

def on_message_received(client, userdata, msg):
    """
    Callback para procesar mensajes recibidos.
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

        detection_id = payload.get("id", "N/A")
        material = payload.get("material", "Unknown")

        logger.info(f"[MAIN] Mensaje recibido | ID: {detection_id} | Material: {material}")

        if material in ["PET", "HDPE"]:
            action_time = round(random.uniform(1, 5), 2)
            action_payload = {
                "id": detection_id,
                "tipo": material,
                "tiempo": action_time
            }

            mqtt_handler.publish("valvula/accion", json.dumps(action_payload))
            logger.info(f"[MAIN] Acción enviada | ID: {detection_id} | Tipo: {material} | Tiempo: {action_time}s")
        else:
            logger.info(f"[MAIN] Material '{material}' ignorado | ID: {detection_id}")

    except Exception as e:
        logger.error(f"[MAIN] Error procesando mensaje: {e}")

def main():
    try:
        # Configuración
        config_path = "/home/raspberry-1/capstonepupr/src/tst/configs/pi1_config.yaml"
        config_manager = ConfigManager(config_path)

        # Configurar logger global
        global logger
        logger = setup_logger("[MAIN PI1]", config_manager.get("logging", {}))

        logger.info("=" * 70)
        logger.info("[MAIN] Iniciando sistema de detección de materiales en Raspberry Pi 1")
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

        logger.info("[MAIN] Esperando señales MQTT de Raspberry-3...")
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