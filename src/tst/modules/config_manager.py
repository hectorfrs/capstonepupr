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
        self.config = {}

        # Logger temporal antes de inicializar LoggingManager
        self.temp_logger = logging.getLogger("[CONFIG_MANAGER]")
        self.temp_logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        self.temp_logger.addHandler(console_handler)

        # Inicializar logger principal
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
                self.logger.debug(f"Contenido de la configuración: {self.config}")
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
        """
        Obtiene un valor de configuración basado en una ruta clave jerárquica.
        :param key_path: Ruta de la clave, separada por puntos (e.g., "mux.activation_time_min").
        :param default: Valor predeterminado si la clave no existe.
        :return: Valor asociado a la clave o el valor predeterminado.
        """
        keys = key_path.split(".")
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except KeyError:
            (self.logger if hasattr(self, "logger") else self.temp_logger).warning(
                f"Clave faltante: {key_path}. Usando valor predeterminado: {default}"
            )
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
