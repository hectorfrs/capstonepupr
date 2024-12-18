# main_pi1.py - Script principal para Raspberry Pi 1
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import time
import json
import random

class MainPI1:
    """
    Script principal para manejar las operaciones del sistema en Raspberry Pi 1.
    """

    def __init__(self, config_manager):
        """
        Inicializa el script principal con configuraciones centralizadas.

        :param config_manager: Instancia de ConfigManager para manejar configuraciones.
        """
        from modules.logging_manager import LoggingManager
        from modules.mqtt_handler import MQTTHandler
        from modules.network_manager import NetworkManager
        from modules.real_time_config import RealTimeConfigManager

        self.config_manager = config_manager
        self.logger = LoggingManager(config_manager).setup_logger("[MAIN_PI1]")
        self.mqtt_handler = MQTTHandler(config_manager)
        self.network_manager = NetworkManager(config_manager)
        self.real_time_config = RealTimeConfigManager(config_manager, self.mqtt_handler)

    def on_message_received(self, client, userdata, msg):
        """
        Callback para procesar mensajes recibidos por MQTT.
        """
        try:
            raw_payload = msg.payload.decode()
            self.logger.info(f"[MQTT] Mensaje recibido en '{msg.topic}': {raw_payload}")

            if not raw_payload.strip():
                self.logger.warning("[MAIN] Mensaje recibido está vacío.")
                return

            try:
                payload = json.loads(raw_payload)
                self.logger.info(f"[MAIN] Mensaje recibido | Tópico: {msg.topic} | Payload: {payload}")
            except json.JSONDecodeError as e:
                self.logger.error(f"[MAIN] Error decodificando JSON: {e}")
                return

            detection_id = payload.get("id", "N/A")
            material = payload.get("material", "Unknown")

            self.logger.info(f"[MAIN] Mensaje recibido | ID: {detection_id} | Material: {material}")

            if material in ["PET", "HDPE"]:
                action_time = round(random.uniform(1, 5), 2)
                action_payload = {
                    "id": detection_id,
                    "tipo": material,
                    "tiempo": action_time
                }

                self.mqtt_handler.publish("valvula/accion", json.dumps(action_payload))
                self.logger.info(f"[MAIN] Acción enviada | ID: {detection_id} | Tipo: {material} | Tiempo: {action_time}s")
            else:
                self.logger.info(f"[MAIN] Material '{material}' ignorado | ID: {detection_id}")

        except Exception as e:
            self.logger.error(f"[MAIN] Error procesando mensaje: {e}")

    def start(self):
        """
        Inicia las operaciones principales del sistema.
        """
        try:
            self.logger.info("=" * 70)
            self.logger.info("[MAIN] Iniciando sistema de detección de materiales en Raspberry Pi 1")
            self.logger.info("=" * 70)

            # Iniciar monitoreo dinámico de configuración
            self.real_time_config.start_monitoring()

            # Configuración de red
            self.logger.info("[MAIN] [NET] Iniciando monitoreo de red...")
            self.network_manager.start_monitoring()

            # Configurar MQTT
            self.logger.info("[MAIN] [MQTT] Configurando cliente MQTT...")
            self.mqtt_handler.client.on_message = self.on_message_received

            self.mqtt_handler.connect()
            self.mqtt_handler.subscribe("material/entrada")

            self.logger.info("[MAIN] Esperando señales MQTT de Raspberry-3...")
            self.mqtt_handler.forever_loop()

        except KeyboardInterrupt:
            self.logger.info("[MAIN] Apagando monitoreo del sistema...")
            self.network_manager.stop_monitoring()
            self.logger.info("[MAIN] Sistema apagado correctamente.")
        except Exception as e:
            self.logger.error(f"[MAIN] Error crítico en la ejecución: {e}")
        finally:
            self.logger.info("[MAIN] Finalizando ejecución del script.")
            if self.mqtt_handler.is_connected():
                self.logger.info("[MAIN] Desconectando cliente MQTT...")
                self.mqtt_handler.disconnect()
                self.logger.info("[MAIN] Cliente MQTT desconectado.")
