# main_pi2.py - Script principal para Raspberry Pi 2
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import time
import json
import random
import sys
from datetime import datetime
from modules.logging_manager import LoggingManager
from modules.network_manager import NetworkManager
from modules.real_time_config import RealTimeConfigManager
from modules.config_manager import ConfigManager
from modules.mqtt_handler import MQTTHandler
from raspberry_pi.pi2.sim.relay_controller import RelayController # Cambiar a la línea de abajo para usar el controlador real
#from raspberry_pi.pi2.lib.relay_controller import RelayController # Cambiar a la línea de arriba para usar el controlador simulado

def clear_cache():
    """
    Limpia la caché del sistema antes de iniciar el script.
    """
    try:
        # Elimina variables residuales del entorno (si aplica)
        logging.debug("[CACHE] Limpiando variables globales...")
        globals().clear()

        # Reinicia el bus I²C (si aplica)
        logging.debug("[CACHE] Reiniciando bus I²C...")
        os.system("i2cdetect -y 1 > /dev/null 2>&1")

        # Libera caché de Python (si es necesario)
        logging.debug("[CACHE] Forzando recolección de basura...")
        import gc
        gc.collect()

        # Opcional: Elimina posibles cachés de bibliotecas
        logging.debug("[CACHE] Eliminando archivos .pyc...")
        pycache_path = os.path.join(os.path.dirname(__file__), "__pycache__")
        if os.path.exists(pycache_path):
            import shutil
            shutil.rmtree(pycache_path)
        logging.info("[CACHE] Limpieza completada.")
    except Exception as e:
        logging.error(f"[CACHE] Error durante la limpieza de caché: {e}")


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

def on_message_received(client, userdata, msg, relay_controller, config):
    """
    Procesa mensajes MQTT en Raspberry 2.
    """
    try:
        payload = json.loads(msg.payload.decode())

        # Extraer datos del mensaje
        event_id = payload.get("id", "Sin ID")
        timestamp = payload.get("timestamp", "Sin Timestamp")
        material = payload.get("material", "Desconocido")

        logger.info(f"[RPI2] Evento recibido | ID: {event_id} | Material: {material} | Timestamp: {timestamp}")

        # Buscar relé asignado al material
        relays = config["mux"]["relays"]
        relay_data = next((relay for relay in relays if relay.get("assigned_material") == material), None)

        if relay_data:
            activation_time_min = relay_data.get("activation_time_min", 0.5)
            activation_time_max = relay_data.get("activation_time_max", 3.0)
            activation_time = round(random.uniform(activation_time_min, activation_time_max), 2)

            # Activar el relé
            relay_index = relay_data["mux_channel"]
            relay_controller.activate_relay(relay_index, activation_time)
            logger.info(f"[RPI2] Relay {relay_index} activado para {material} por {activation_time} segundos. ID Evento: {event_id}")
        else:
            logger.warning(f"[RPI2] Material desconocido o no asignado: {material}. ID Evento: {event_id}")

    except json.JSONDecodeError as e:
        logger.error(f"[RPI2] Error decodificando JSON: {e}")
    except Exception as e:
        logger.error(f"[RPI2] Error procesando mensaje: {e}")


def main():
    # Inicialización de variables
    network_manager = None  # Inicialización para evitar errores de referencia
    relay_controller = None  # Inicialización para evitar errores de referencia
    # Configuración
    config_path = "/home/raspberry-2/capstonepupr/src/tst/configs/pi2_config.yaml"
    try:
        config_manager = ConfigManager(config_path)
        logging_manager = LoggingManager(config_manager)
        time.sleep(0.5)
    except Exception as e:
        logger.error(f"Error inicializando ConfigManager: {e}")
        raise
    
    # Inicializar logger básico para respaldo en caso de fallos
    logger = logging_manager.setup_logger("[MAIN PI-2]")
    try:
        logger.info("=" * 70)
        logger.info("Iniciando sistema de control de Relay en Raspberry Pi 2")
        logger.info("=" * 70)

        # Cargar configuración dinámica
        logger.info("Iniciando monitoreo de configuración en tiempo real...")
        real_time_config = RealTimeConfigManager(config_manager)
        real_time_config.start_monitoring()
        config = real_time_config.get_config()
        time.sleep(0.5)

        # Limpieza de caché
        #clear_cache()
        

        # Configuración de red
        logger.info("Iniciando monitoreo de red...")
        network_manager = NetworkManager(config)
        network_manager.start_monitoring()

        # Obtener velocidad del conveyor y distancias configuradas
        conveyor_speed = config["system"].get("conveyor_speed", 100)
        distances = config.get("delays", {})

        # Calcular delays
        delay_sensor_to_valve_1 = calculate_delay(distances["sensor_to_valve_1"], conveyor_speed)
        delay_sensor_to_valve_2 = calculate_delay(distances["sensor_to_valve_2"], conveyor_speed)

        logger.info(f"[PI2] Delay sensor a válvula 1: {delay_sensor_to_valve_1} segundos")
        logger.info(f"[PI2] Delay sensor a válvula 2: {delay_sensor_to_valve_2} segundos")

        # Configuración de relay
        logger.info("[PI2] Configurando controlador de relay...")
        relay_config = config.get("mux", {}).get("relays", [])
        if not isinstance(relay_config, list):
            raise ValueError("[PI2] La configuración de relays debe ser una lista.")

        relay_controller = RelayController(relay_config)

        # Inicializa MQTTHandler
        mqtt_handler = MQTTHandler(config_manager)

        # Asigna el callback personalizado
        mqtt_handler.client.on_message = lambda client, userdata, msg: on_message_received(
    client, userdata, msg, relay_controller, config_manager
)

        # Conecta al broker MQTT y suscribe a tópicos
        mqtt_handler.connect_and_subscribe()

        # Publicación de prueba
        #mqtt_handler.publish("valvula/estado", "Iniciando monitoreo")

        # Loop continuo para mensajes
        logger.info("Esperando mensajes MQTT de Raspberry 1...")
        mqtt_handler.client.loop_forever()


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
    global relay_controller
    global logger
