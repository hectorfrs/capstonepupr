# main.py - Script principal para el control de relés y la comunicación MQTT    
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import json
import logging
from utils.mqtt_client import create_mqtt_client, subscribe_to_topic, publish_message, Client, MQTTv311
from lib.relay_controller import RelayController
from utils.network_manager import NetworkManager
from utils.real_time_config import RealTimeConfigManager
from utils.config_manager import ConfigManager

def main():
    try:
        # Cargar configuración
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s' , datefmt='%Y-%m-%d %H:%M:%S')
        config_path = "/home/raspberry-2/capstonepupr/src/pi2/config/config.yaml"

        # Configuración de BucketLogger
        bucket_logger = logging.getLogger("BucketLogger")
        bucket_logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler("/home/raspberry-2/logs/bucket_status.log")
        file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
        bucket_logger.addHandler(file_handler)

        # Registro en BucketLogger
        bucket_logger.info(f"[BUCKET] {material_type} | ID: {detection_id} | Peso total actual: {current_weight}g")


        # Configuración
        logging.info("=" * 80)
        logging.info("        [MAIN] Iniciando sistema de control de Relay")
        logging.info("=" * 80)

        logging.info("[MAIN] Cargando configuración...")
        config_manager = RealTimeConfigManager(config_path)
        logging.info("[MAIN] Iniciando monitoreo de configuración...")
        config_manager.start_monitoring()
        config = config_manager.get_config()

        # Configuración de red
        logging.info("[MAIN] Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        # Inicializar el controlador de relés con la configuración desde config.yaml
        logging.info("[MAIN] Inicializando controlador de relés...")
        relay_controller = RelayController(config['mux']['relays'])

        # Variables de configuración MQTT
        logging.info("[MAIN] Inicializando cliente MQTT...")
        broker_addresses = config['mqtt']['broker_addresses']
        port = config['mqtt']['port']
        client_id = config['mqtt']['client_id']
        topic_action = config['mqtt']['topics']['action']
        topic_status = config['mqtt']['topics']['status']

        # Función para manejar el control de los relés según el tipo de material
        def handle_relay_control(material_type, duration):
            if material_type == 'PET':
                relay_controller.activate_relay(0, duration)  # Activar relé 1
                logging.info(f"[MAIN] [RELAY] Activando Relay 1 (PET) por {duration} segundos")
            elif material_type == 'HDPE':
                relay_controller.activate_relay(1, duration)  # Activar relé 2
                logging.info(f"[MAIN] [RELAY] Activando Relay 2 (HDPE) por {duration} segundos")
            else:
                logging.info(f"[MAIN] [RELAY] Material desconocido: {material_type}")

        # Callback para manejar mensajes MQTT
        def on_message(client, userdata, msg):
            payload = json.loads(msg.payload.decode())
            if msg.topic == topic_action:
                material_type = payload.get('tipo')
                duration = payload.get('tiempo')
                if material_type and duration:
                    handle_relay_control(material_type, duration)
                    # Publicar estado del relé
                    client.publish(topic_status, json.dumps({'bucket_info': f'Bucket para {material_type}'}))

        def on_message_received(client, userdata, msg):
            """
            Callback para procesar mensajes MQTT y activar relés.
            """
            try:
                payload = json.loads(msg.payload.decode())
                detection_id = payload.get("id", "N/A")
                material_type = payload.get("tipo")
                action_time = payload.get("tiempo")

                if material_type and action_time:
                    logging.info(f"[MAIN] Señal recibida | ID: {detection_id} | Material: {material_type} | Tiempo: {action_time}s")

                    # Activar relé correspondiente
                    if material_type == "PET":
                        relay_controller.activate_relay(0, action_time)
                    elif material_type == "HDPE":
                        relay_controller.activate_relay(1, action_time)

                    logging.info(f"[MAIN] Relé activado | ID: {detection_id} | Material: {material_type} | Tiempo: {action_time}s")
                else:
                    logging.warning(f"[MAIN] Mensaje inválido recibido: {payload}")

            except Exception as e:
                logging.error(f"[MAIN] Error al procesar mensaje: {e}")



        # Crear cliente MQTT
        logging.info("[MAIN] Conectando al broker MQTT...")
        mqtt_client = create_mqtt_client(client_id, broker_addresses, port, config['mqtt']['keepalive'], on_message)

        # Suscribirse al tema de acción
        logging.info(f"[MAIN] Suscribiéndose al tema {topic_action}")
        subscribe_to_topic(mqtt_client, topic_action)
        #mqtt_client.on_subscribe = lambda client, userdata, mid, granted_qos: print(f"[MAIN] [MQTT] Suscripción exitosa.")

        # Iniciar bucle MQTT
        logging.info("[MAIN] Esperando señales desde Raspberry Pi 1...")
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        logging.info("[MAIN] Apagando Monitoreo del Network...")
        network_manager.stop_monitoring()
        logging.info("[MAIN] Sistema apagado correctamente.")
    except Exception as e:
        logging.error(f"[MAIN] Error crítico en la ejecución: {e}")
    finally:
        logging.info("[MAIN] Finalizando ejecución del script.")
        mqtt_client.disconnect()
        logging.info("[MAIN] Cliente MQTT desconectado.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error crítico en la ejecución: {e}")
