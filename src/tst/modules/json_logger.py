# json_logger.py - Clase para registrar datos en formato JSON.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import os
import json
from datetime import datetime

class JSONLogger:
    """
    Clase para manejar el registro de datos en formato JSON.
    """

    def __init__(self, config_manager):
        """
        Inicializa el JSONLogger con configuraciones centralizadas.

        :param config_manager: Instancia de ConfigManager para manejar configuraciones.
        """
        from modules.logging_manager import LoggingManager

        self.config_manager = config_manager
        self.logger = LoggingManager(config_manager).setup_logger("[JSON_LOGGER]")

    def log_data(self, data, file_key="logging.json_file"):
        """
        Registra datos en un archivo JSON con una estructura definida.

        :param data: Diccionario con los datos a registrar.
        :param file_key: Clave en la configuración para determinar la ruta del archivo de log.
        """
        try:
            file_path = self.config_manager.get(file_key, "logs/data.json")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "a") as json_file:
                json.dump(data, json_file)
                json_file.write("\n")

            self.logger.info(f"Datos registrados exitosamente en {file_path}.")
        except Exception as e:
            self.logger.error(f"Error registrando datos en JSON: {e}")

    def log_event(self, event, metadata=None):
        """
        Registra un evento con metadatos en el archivo de log JSON.

        :param event: Nombre o tipo de evento.
        :param metadata: Diccionario con información adicional del evento.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "metadata": metadata or {}
        }
        self.log_data(log_entry)
