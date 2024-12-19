# config_manager.py - Clase para manejar la configuración del sistema desde un archivo YAML.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import yaml
import os

class ConfigManager:
    """
    Clase para manejar la configuración del sistema desde un archivo YAML.
    """

    def __init__(self, config_path):
        """
        Inicializa el ConfigManager cargando la configuración desde el archivo YAML.

        :param config_path: Ruta al archivo YAML.
        """
        from modules.logging_manager import LoggingManager

        self.config_path = config_path
        self.config = {}

        # Inicializa el logger antes de usarlo
        logging_manager = LoggingManager(self)
        self.logger = logging_manager.setup_logger("[CONFIG_MANAGER]")

        # Cargar configuración inicial
        self.load_config()
        self.validate_config()

    def load_config(self):
        """
        Carga la configuración desde un archivo YAML. Si no existe, utiliza valores predeterminados.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as file:
                    self.config = yaml.safe_load(file)
                    self.logger.info(f"Configuración cargada desde {self.config_path}")
            else:
                self.logger.warning(f"El archivo de configuración no existe: {self.config_path}. Usando valores predeterminados.")
                self.config = {}
        except yaml.YAMLError as e:
            self.logger.error(f"Error al leer el archivo YAML: {e}. Usando configuración predeterminada.")
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
        Obtiene un valor de configuración dado su ruta en el diccionario.

        :param key_path: Ruta de la clave (por ejemplo, "system.enable_sensors").
        :param default: Valor predeterminado si la clave no existe.
        :return: Valor de configuración o el predeterminado.
        """
        keys = key_path.split(".")
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                self.logger.warning(f"Clave no encontrada: {key_path}. Usando valor predeterminado: {default}")
                return default
        self.logger.debug(f"Valor encontrado para {key_path}: {value}")
        return value

    def set(self, key_path, value):
        """
        Establece un valor en la configuración y lo guarda.

        :param key_path: Ruta de la clave (por ejemplo, "system.enable_sensors").
        :param value: Valor a establecer.
        """
        keys = key_path.split(".")
        config_section = self.config
        for key in keys[:-1]:
            config_section = config_section.setdefault(key, {})
        config_section[keys[-1]] = value
        self.save_config()
        self.logger.info(f"Configuración actualizada: {key_path} = {value}")

    def validate_config(self):
        """
        Valida la configuración actual para asegurarse de que contenga todas las claves requeridas.
        Si faltan claves, establece valores predeterminados.
        """
        logger.info("Validando configuración...")
        required_keys = {
            "system.enable_sensors": True,
            "system.enable_logging": True,
            "logging.log_file": "logs/app.log",
            "mqtt.enable_mqtt": True,
        }

        for key, default_value in required_keys.items():
            if self.get(key) is None:
                self.set(key, default_value)
                self.logger.warning(f"Clave faltante en la configuración: {key}. Valor predeterminado establecido: {default_value}")
