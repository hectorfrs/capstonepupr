#main.py - Simulación de detección de materiales en una planta de reciclaje
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import time
import json
import logging
import yaml
import os
import paho.mqtt.client as mqtt
from utils.network_manager import NetworkManager
from utils.real_time_config import RealTimeConfigManager
from utils.config_manager import ConfigManager
from utils.mqtt_publisher import start_publisher
from utils.mqtt_client import create_mqtt_client, publish_message, subscribe_to_topic

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

# Función para cargar configuración desde config.yaml
def load_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    else:
        raise FileNotFoundError(f"[ERROR] No se encontró el archivo de configuración: {config_path}")

# Función principal
def main():
    try:
        # Ruta del archivo de configuración

        # Cargar configuración
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s' , datefmt='%Y-%m-%d %H:%M:%S')
        config_path = "/home/raspberry-1/capstonepupr/src/pi1/config/config.yaml"
        
        # Configuración
        logging.info("=====================================================================")
        logging.info("    [MAIN] Iniciando sistema de detección de materiales")
        logging.info("=====================================================================")

        logging.info("[MAIN] Cargando configuración...")
        config_manager = RealTimeConfigManager(config_path)
        logging.info("[MAIN] Iniciando monitoreo de configuración...")
        config_manager.start_monitoring()
        config = config_manager.get_config()

        # Configuración de red
        logging.info("[MAIN] Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        # Configuración MQTT
        broker_addresses = config["mqtt"]["broker_addresses"]
        port = config["mqtt"]["port"]
        keepalive = config["mqtt"]["keepalive"]
        client_id = config["mqtt"]["client_id"]
        topic_action = config["mqtt"]["topics"]["action"]

        # Crear el cliente MQTT (usando mqtt_client.py)
        logging.info("[MAIN] Inicializando cliente MQTT...")
        mqtt_client = create_mqtt_client(client_id, broker_addresses, port, keepalive)
        logging.info("[MAIN] Cliente MQTT conectado exitosamente.")

        # Iniciar la simulación de detección de materiales (usando mqtt_publisher.py)
        logging.info("[MAIN] Iniciando simulación de detección de materiales...")
        start_publisher(mqtt_client, topic_action, config["simulation"])

    except KeyboardInterrupt:
        logging.info("[MAIN] Simulación detenida por el usuario.")
    except Exception as e:
        logging.error(f"[MAIN] Error crítico en la ejecución: {e}")
    finally:
        logging.info("[MAIN] Finalizando ejecución del script.")

if __name__ == "__main__":
    main()
