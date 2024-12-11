
# config_manager.py - Clase para manejar la configuración del sistema.
# Desarrollado por Hector F. Rivera Santiago
# Copyright (c) 2024

import yaml
import logging

class ConfigManager:
    """Clase para manejar la configuración del sistema."""

    def __init__(self, config_path="pi1_config_optimized.yaml"):
        """
        Inicializa el gestor de configuración.
        :param config_path: Ruta al archivo de configuración YAML.
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """Carga la configuración desde el archivo YAML."""
        try:
            with open(self.config_path, "r") as file:
                config = yaml.safe_load(file)
                logging.info("Archivo de configuración cargado correctamente.")
                return config
        except Exception as e:
            logging.error(f"Error al cargar el archivo de configuración: {e}")
            raise

    def get(self, key, default=None):
        """
        Obtiene un valor de configuración dado un key.
        :param key: Clave de configuración.
        :param default: Valor predeterminado si no se encuentra el key.
        :return: Valor de la configuración.
        """
        return self.config.get(key, default)

    @staticmethod
    def setup_logging(logging_config):
        """
        Configura el logging basado en el archivo de configuración.
        :param logging_config: Diccionario con la configuración de logging.
        """
        level = logging_config.get("level", "DEBUG").upper()
        log_file = logging_config.get("file", "app.log")

        logging.basicConfig(
            level=getattr(logging, level, logging.DEBUG),
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        logging.info("Logging configurado correctamente.")
