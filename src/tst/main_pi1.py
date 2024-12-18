# main.py - Simulación de detección de materiales en una planta de reciclaje
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

# main.py - Script principal para Raspberry Pi 1
import time
import json
import logging
import yaml
import os
import random  # Importar random
import paho.mqtt.client as mqtt
from modules.network_manager import NetworkManager
from modules.real_time_config import RealTimeConfigManager
from modules.config_manager import ConfigManager
from modules.mqtt_handler import MQTTHandler
from modules.logging_manager import setup_logger

# Función para manejar mensajes recibidos desde material/entrada
def on_message(client, userdata, msg):
    logging.info(f"[MQTT] Mensaje recibido en {msg.topic}: {msg.payload.decode()}")

    try:
        # Decodificar mensaje
        payload = json.loads(msg.payload.decode())
        material = payload.get("material", "")
        timestamp = payload.get("timestamp", "")

        logging.info(f"[MAIN] Material detectado: {material} a las {timestamp}")

        # Solo procesar materiales PET o HDPE
        if material in ["PET", "HDPE"]:
            duration = round(random.uniform(1, 5), 2)  # Tiempo aleatorio entre 1 y 5 segundos
            action_message = {"tipo": material, "tiempo": duration}

            # Publicar en valvula/accion
            client.publish("valvula/accion", json.dumps(action_message))
            logging.info(f"[MAIN] Publicado en 'valvula/accion': {action_message}")
        else:
            logging.info(f"[MAIN] Material '{material}' no relevante para activación de relés.")

    except Exception as e:
        logging.error(f"[MAIN] Error procesando mensaje: {e}")

def on_message_received(client, userdata, msg):
    """
    Callback para procesar mensajes recibidos.
    """
    try:
        # Decodificar el payload
        raw_payload = msg.payload.decode()
        logging.info(f"[MQTT] Mensaje recibido en '{msg.topic}': {raw_payload}")

        # Validar si el payload es JSON válido
        if not raw_payload.strip():
            logging.warning("[MAIN] Mensaje recibido está vacío.")
            return

        try:
            payload = json.loads(raw_payload)
            logging.info(f"[MAIN] Mensaje recibido | Tópico: {msg.topic} | Payload: {payload}")
        except json.JSONDecodeError as e:
            logging.error(f"[MAIN] Error decodificando JSON: {e}")
            return

        # Obtener parámetros
        detection_id = payload.get("id", "N/A")
        material = payload.get("material", "Unknown")

        logging.info(f"[MAIN] Mensaje recibido | ID: {detection_id} | Material: {material}")

        # Verificar si el material es válido
        if material in ["PET", "HDPE"]:
            action_time = round(random.uniform(1, 5), 2)
            action_payload = {
                "id": detection_id,
                "tipo": material,
                "tiempo": action_time
            }

            # Publicar mensaje para activar válvula
            publish_message(client, "valvula/accion", action_payload)
            logging.info(f"[MAIN] Acción enviada | ID: {detection_id} | Tipo: {material} | Tiempo: {action_time}s")
        else:
            logging.info(f"[MAIN] Material '{material}' ignorado | ID: {detection_id}")

    except Exception as e:
        logging.error(f"[MAIN] Error procesando mensaje: {e}")


# Función principal
def main():
    try:
        # Cargar configuración desde el archivo YAML
        config_path = ConfigManager("/home/raspberry-1/capstonepupr/src/tst/configs/pi1_config.yaml").config
        config_manager = RealTimeConfigManager(config_path)
        config_manager.start_monitoring()
        config = config_manager.get_config()

        # Inicializar el logger global
        logger = setup_logger(["MAIN PI1"], config.get("logging", {}))

        # Configuración
        logging.info("=" * 70)
        logging.info("[MAIN] Iniciando sistema de detección de materiales en Raspberry Pi 1")
        logging.info("=" * 70)

        # Cargar configuración
        
        config_manager = RealTimeConfigManager(config_path)
        config_manager.start_monitoring()
        config = config_manager.get_config()

        # Configuración de red
        logging.info("[MAIN] [NET] Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        # Inicializar el manejador MQTT
        logging.info("[MAIN] [MQTT] Configurando cliente MQTT...")
        mqtt_config = config["mqtt"]
        mqtt_handler = MQTTHandler(mqtt_config)
        mqtt_handler.client.on_message = on_message_received  # Asignar el callback

        
        # Conectar al broker
        try:
            mqtt_handler.connect()
        except ConnectionError as e:
            logging.critical(f"[MAIN] No se pudo conectar a ningún broker MQTT: {e}")
            exit(1)
        logging.info("[MAIN] [MQTT] Conectado al broker MQTT.")

        # Suscribirse a los tópicos
        #topics = [mqtt_config["topics"]["entry"], mqtt_config["topics"]["detection"]]
        #mqtt_handler.subscribe(topics)

        mqtt_handler.subscribe("material/entrada")
        mqtt_handler.subscribe_multiple({
            "material/entrada": on_message_received
        })

        # Iniciar bucle infinito
        logging.info("[MAIN] Esperando señales MQTT de Raspberry-3...")
        mqtt_handler.forever_loop()

    except KeyboardInterrupt:
        logging.info("[MAIN] Apagando Monitoreo del Network...")
        network_manager.stop_monitoring()
        logging.info("[MAIN] Sistema apagado correctamente.")
    except Exception as e:
        logging.error(f"[MAIN] Error crítico en la ejecución: {e}")
    finally:
        logging.info("[MAIN] Finalizando ejecución del script.")
        if 'mqtt_handler' in locals() and mqtt_handler.is_connected():
            logging.info("[MAIN] Desconectando cliente MQTT...")
        mqtt_handler.disconnect()
        logging.info("[MAIN] Cliente MQTT desconectado.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error crítico en la ejecución: {e}")
