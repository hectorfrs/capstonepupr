# json_manager.py - Manejo centralizado de datos JSON para almacenamiento y recuperación.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import json
import os
from datetime import datetime
import uuid
from modules.logging_manager import setup_logger
from modules.config_manager import ConfigManager

class JSONManager:
    """
    Clase para manejar operaciones relacionadas con datos JSON.
    """

    def __init__(self, config_manager):
        """
        Inicializa el JSONManager con configuraciones centralizadas.

        :param config_manager: Instancia de ConfigManager para manejar configuraciones.
        """
        self.config_manager = config_manager
        self.logger = setup_logger("[JSON_MANAGER]", config_manager.get("logging", {}))

    def generate_json(self, sensor_id, channel, spectral_data, detected_material, confidence):
        """
        Genera un objeto JSON para representar los datos de medición.

        :param sensor_id: ID del sensor que tomó la medición.
        :param channel: Canal del MUX correspondiente.
        :param spectral_data: Diccionario con valores espectrales.
        :param detected_material: Material identificado.
        :param confidence: Nivel de confianza en la clasificación.
        :return: Diccionario JSON con un ID único.
        """
        self.logger.info("Generando JSON con los datos de medición.")
        return {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "sensor_id": sensor_id,
            "channel": channel,
            "spectral_data": spectral_data,
            "detected_material": detected_material,
            "confidence": confidence
        }

    def save_json(self, data, file_path_key="logging.json_file"):
        """
        Guarda un objeto JSON en un archivo.

        :param data: Objeto JSON a guardar.
        :param file_path_key: Clave en la configuración para obtener la ruta del archivo.
        """
        try:
            file_path = self.config_manager.get(file_path_key, "logs/data.json")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Crear el directorio si no existe

            with open(file_path, "a") as file:
                file.write(json.dumps(data) + "\n")

            self.logger.info(f"Datos guardados en {file_path}.")
        except Exception as e:
            self.logger.error(f"Error guardando datos en {file_path}: {e}")

    def load_json(self, file_path_key="logging.json_file"):
        """
        Carga datos JSON desde un archivo.

        :param file_path_key: Clave en la configuración para obtener la ruta del archivo.
        :return: Lista de objetos JSON.
        """
        try:
            file_path = self.config_manager.get(file_path_key, "logs/data.json")

            if not os.path.exists(file_path):
                self.logger.warning(f"El archivo {file_path} no existe.")
                return []

            with open(file_path, "r") as file:
                self.logger.info(f"Cargando datos desde {file_path}.")
                return [json.loads(line) for line in file.readlines()]
        except Exception as e:
            self.logger.error(f"Error cargando datos desde {file_path}: {e}")
            return []

    def clean_json(self, file_path_key="logging.json_file"):
        """
        Limpia el contenido de un archivo JSON.

        :param file_path_key: Clave en la configuración para obtener la ruta del archivo.
        """
        try:
            file_path = self.config_manager.get(file_path_key, "logs/data.json")

            if os.path.exists(file_path):
                with open(file_path, "w") as file:
                    file.truncate(0)
                self.logger.info(f"El archivo {file_path} ha sido limpiado.")
            else:
                self.logger.warning(f"El archivo {file_path} no existe.")
        except Exception as e:
            self.logger.error(f"Error limpiando el archivo {file_path}: {e}")
