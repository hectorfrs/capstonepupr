# json_logger.py - Manejo centralizado de datos JSON para almacenamiento y transmisión.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import os
import json
from datetime import datetime
import uuid

class JSONLogger:
    """
    Clase para manejar operaciones relacionadas con datos JSON.
    """

    def __init__(self, config_manager, mqtt_handler=None):
        """
        Inicializa el JSONLogger con configuraciones centralizadas.

        :param config_manager: Instancia de ConfigManager para manejar configuraciones.
        :param mqtt_handler: Instancia opcional de MQTTHandler para transmitir datos JSON.
        """
        from modules.logging_manager import LoggingManager

        self.config_manager = config_manager
        self.mqtt_handler = mqtt_handler
        self.enable_logging = self.config_manager.get("system.enable_json_logging", True)
        self.logger = LoggingManager(config_manager).setup_logger("[JSON_LOGGER]")

    def log_data(self, data, file_path_key="logging.json_file"):
        """
        Registra datos en un archivo JSON con una estructura definida.

        :param data: Diccionario con los datos a registrar.
        :param file_path_key: Clave en la configuración para determinar la ruta del archivo de log.
        """
        if not self.enable_logging:
            self.logger.warning("El registro de datos JSON está deshabilitado en la configuración.")
            return

        try:
            file_path = self.config_manager.get(file_path_key, "logs/data.json")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "a") as json_file:
                json.dump(data, json_file)
                json_file.write("\n")

            self.logger.info(f"Datos registrados exitosamente en {file_path}.")

            # Publicar datos mediante MQTT si está habilitado
            if self.mqtt_handler and self.mqtt_handler.is_connected():
                self.mqtt_handler.publish("data/json", data)
        except Exception as e:
            self.logger.error(f"Error registrando datos en JSON: {e}")

    def log_event(self, event, metadata=None):
        """
        Registra un evento con metadatos en el archivo de log JSON.

        :param event: Nombre o tipo de evento.
        :param metadata: Diccionario con información adicional del evento.
        """
        if not self.enable_logging:
            self.logger.warning("El registro de eventos está deshabilitado en la configuración.")
            return

        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "metadata": metadata or {}
        }
        self.log_data(log_entry)
