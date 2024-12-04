import yaml
import os
import logging

class ConfigManager:
    """
    Clase para manejar la carga y validación de archivos de configuración YAML.
    """
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        """
        Carga un archivo de configuración YAML.
        
        :return: Diccionario con la configuración cargada.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"El archivo de configuración no existe: {self.config_path}")

        with open(self.config_path, "r") as file:
            try:
                config = yaml.safe_load(file)
                logging.info(f"Archivo de configuración cargado correctamente desde {self.config_path}.")
                return config
            except yaml.YAMLError as e:
                logging.error(f"Error al cargar el archivo YAML: {e}")
                raise

    def validate_config(self, default_values):
        """
        Valida y asigna valores predeterminados a las claves faltantes en la configuración.

        :param default_values: Diccionario con los valores predeterminados.
        """
        def recursive_update(d, defaults):
            for key, value in defaults.items():
                if key not in d:
                    d[key] = value
                elif isinstance(value, dict):
                    recursive_update(d[key], value)

        logging.info("Validando configuración...")
        recursive_update(self.config, default_values)

    def get(self, key, default=None):
        """
        Obtiene un valor de la configuración con soporte para claves anidadas.

        :param key: Clave para buscar en la configuración (ejemplo: "system.enable_sensors").
        :param default: Valor predeterminado si la clave no existe.
        :return: Valor correspondiente a la clave.
        """
        keys = key.split(".")
        value = self.config
        for k in keys:
            value = value.get(k, default)
            if value is default:
                break
        return value
