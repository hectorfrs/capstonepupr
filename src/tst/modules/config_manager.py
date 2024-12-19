# config_manager.py - Clase para manejar la configuración del sistema desde un archivo YAML.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import yaml
import os
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
        self.config = {}

        # Inicializar logger
        logging_manager = LoggingManager(self)
        self.logger = logging_manager.setup_logger("[CONFIG_MANAGER]")

        # Cargar y validar configuración
        self.load_config()
        self.validate_config()

    def load_config(self):
        try:
            with open(self.config_path, "r") as file:
                self.config = yaml.safe_load(file)
                self.logger.info(f"Configuración cargada desde {self.config_path}")
        except FileNotFoundError:
            self.logger.warning(f"El archivo de configuración no existe: {self.config_path}. Usando valores predeterminados.")
            self.config = {}
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            self.config = {}

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
        keys = key_path.split(".")
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

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
        }

        for key, default in required_keys.items():
            if self.get(key, None) is None:
                self.set(key, default)
                self.logger.warning(f"Clave faltante: {key}. Valor predeterminado establecido: {default}")
