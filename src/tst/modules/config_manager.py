# config_manager.py - Clase para manejar la configuración del sistema desde un archivo YAML.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import yaml
import os
import logging
from modules.logging_manager import LoggingManager

class ConfigManager:
    """
    Clase para manejar la configuración del sistema desde un archivo YAML.
    """

    def __init__(self, config_path):
        """
        Inicializa el ConfigManager cargando la configuración desde el archivo YAML.

        :param config_path: Ruta al archivo YAML.
        """
        
        self.config_path = config_path
        self.config_data = self.load_config(self.config_path)

        # Logger temporal antes de inicializar LoggingManager
        self.temp_logger = logging.getLogger("[CONFIG_MANAGER]")
        self.temp_logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        self.temp_logger.addHandler(console_handler)

        # Inicializar logger principal
        try:
            self.logging_manager = LoggingManager(self)
            self.logger = None
        
        except Exception as e:
            # Logger de fallback si falla el setup
            self.logger = logging.getLogger("[CONFIG_MANAGER]")
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            self.logger.warning("Usando logger de fallback debido a errores en LoggingManager.")

        # Cargar y validar configuración
        self.config_data = self.load_config(config_path)
        if not os.path.exists(config_path):
            self.logger.error(f"El archivo de configuración no existe: {config_path}")
        exit(1) 
        self.validate_config()

    def load_config(self, config_path):
        """
        Carga el archivo YAML de configuración.

        :param config_path: Ruta al archivo de configuración YAML.
        :return: Diccionario con los datos de configuración.
        """
        try:
            with open(config_path, 'r') as file:
                config_data = yaml.safe_load(file)
                if not config_data:
                    raise ValueError("El archivo de configuración está vacío.")
                return config_data
        except FileNotFoundError:
            raise FileNotFoundError(f"No se pudo encontrar el archivo de configuración: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error al parsear el archivo YAML: {e}")

    def save_config(self):
        """
        Guarda la configuración actual en el archivo YAML.
        """
        try:
            with open(self.config_path, "w") as file:
                yaml.dump(self.config, file, default_flow_style=False)
                self.logger.info(f"Configuración guardada en {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error al guardar la configuración: {e}")

    def get(self, key_path, default=None):
        """
        Obtiene un valor de configuración utilizando una clave jerárquica.

        :param key_path: Ruta de la clave (e.g., 'logging.enable_debug').
        :param default: Valor predeterminado si la clave no existe.
        :return: Valor encontrado o el predeterminado.
        """
        keys = key_path.split('.')
        value = self.config_data
        try:
            for key in keys:
                value = value[key]
            return value
        except KeyError:
            self.logger.warning(f"Clave faltante: {key_path}. Usando valor predeterminado: {default}")
            return default
        except Exception as e:
            self.logger.error(f"Error accediendo a la configuración: {e}")
            return default

    def set(self, key_path, value):
        keys = key_path.split(".")
        config = self.config
        for key in keys[:-1]:
            config = config.setdefault(key, {})
        config[keys[-1]] = value
        self.logger.info(f"Clave configurada: {key_path} = {value}")

    def validate_config(self):
        required_keys = {
            "mqtt.enable_mqtt": True,
            "mqtt.broker_addresses": ["localhost"],
            "logging.enable_debug": False,
            "log_file": "~/logs/app.log",
            "error_log_file": "~/logs/error.log",
        }

        for key, default in required_keys.items():
            if self.get(key, None) is None:
                self.set(key, default)
                print(f"Clave faltante: {key}. Valor predeterminado establecido: {default}")
