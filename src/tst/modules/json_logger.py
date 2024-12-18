# json_logger.py - Clase para registrar datos en formato JSON.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import json
from datetime import datetime
import os
from modules.logging_manager import setup_logger
from modules.config_manager import ConfigManager

class JSONLogger:
    """
    Clase para manejar el registro de datos en formato JSON.
    """
    def __init__(self, config_manager, enable_logging=True):
        """
        Inicializa el JSONLogger con la configuración proporcionada.

        :param config_manager: Instancia de ConfigManager para manejar configuraciones.
        :param enable_logging: Habilita o deshabilita el registro de datos.
        """
        self.config_manager = config_manager
        self.enable_logging = enable_logging

        # Configurar logger centralizado
        self.logger = setup_logger("[JSON_LOGGER]", self.config_manager.get("logging", {}))

    def log_detection(self, data):
        """
        Registra datos en un archivo JSON, agregando un timestamp.

        :param data: Diccionario con los datos a registrar.
        """
        if not self.enable_logging:
            self.logger.warning("El registro de datos JSON está deshabilitado.")
            return

        try:
            # Obtener la ruta del archivo de log desde la configuración
            file_path = self.config_manager.get("logging.log_file", "logs/default_log.json")

            # Agregar timestamp al registro
            data["timestamp"] = datetime.now().isoformat()

            # Crear el directorio si no existe
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Escribir datos en el archivo JSON
            with open(file_path, "a") as f:
                f.write(json.dumps(data) + "\n")

            self.logger.info(f"Datos guardados en {file_path}: {data}")
        except Exception as e:
            self.logger.error(f"Error registrando datos en JSON: {e}")
