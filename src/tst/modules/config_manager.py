# config_manager.py - Manejador de configuraciones centralizadas para el proyecto
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import yaml
import logging
import os
from modules.logging_manager import LoggingManager

class ConfigManager:
    """
    Clase para manejar la configuración centralizada del sistema.
    """

    def __init__(self, config_path):
        """
        Inicializa el manejador de configuraciones.

        :param config_path: Ruta al archivo de configuración YAML.
        """
        self.config_path = config_path
        self.config_data = {}

        # Configurar logger
        try:
            self.logger = LoggingManager(self).setup_logger("[CONFIG_MANAGER]")
        except Exception:
            # Fallback a un logger básico si hay un error en LoggingManager
            logging.basicConfig(level=logging.WARNING, format="%(asctime)s - [%(levelname)s] - %(message)s")
            self.logger = logging.getLogger("[CONFIG_MANAGER]")
            self.logger.warning("Usando logger de fallback debido a errores en LoggingManager.")

        # Cargar configuración
        self.config_data = self.load_config()
        self.validate_config()

    def load_config(self, config_path):
        """
        Carga el archivo de configuración YAML.
        """
        try:
            with open(config_path, "r") as file:
                self.config_data = yaml.safe_load(file)
            logger.info("[CONFIG_MANAGER] Configuración cargada exitosamente.")
            logger.debug(f"[CONFIG_MANAGER] Contenido de la configuración: {self.config_data}")
        except Exception as e:
            logger.error(f"[CONFIG_MANAGER] Error al cargar configuración: {e}")
            raise


    def load_config(self, config_path=None):
        """
        Carga el archivo de configuración YAML.
        """
        try:
            if config_path is None:
                config_path = self.config_path
            with open(config_path, "r") as file:
                self.config_data = yaml.safe_load(file)
            logger.info("[CONFIG_MANAGER] Configuración cargada exitosamente.")
        except Exception as e:
            logger.error(f"[CONFIG_MANAGER] Error al cargar configuración: {e}")
            raise


        return logger

    def validate_config(self):
        """
        Valida y completa claves faltantes en la configuración.
        """
        required_keys = {
            "mqtt.enable_mqtt": True,
            "mqtt.broker_addresses": ["192.168.1.147"],
            "mqtt.port": 1883,
            "mqtt.keepalive": 60,
            "mqtt.topics.entry": "material/entrada",
            "mqtt.topics.detection": "material/deteccion",
            "mqtt.topics.action": "valvula/accion",
            "mqtt.topics.status": "valvula/estado",
            "mqtt.topics.alertas": "raspberry-3/alertas"
        }


        for key, default in required_keys.items():
            if self.get(key, None) is None:
                self.set(key, default)
                self.logger.info(f"Clave faltante: {key}. Valor predeterminado establecido: {default}")

    def get(self, key_path, default=None):
        """
        Obtiene un valor de configuración basado en su clave.

        :param key_path: Clave jerárquica (e.g., "mqtt.enable_mqtt").
        :param default: Valor predeterminado si la clave no existe.
        :return: Valor asociado a la clave o el valor predeterminado.
        """
        keys = key_path.split(".")
        value = self.config_data

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            self.logger.warning(f"Clave faltante: {key_path}. Usando valor predeterminado: {default}")
            return default

    def set(self, key_path, value):
        """
        Establece un valor en la configuración basado en su clave.

        :param key_path: Clave jerárquica (e.g., "mqtt.enable_mqtt").
        :param value: Valor a establecer.
        """
        keys = key_path.split(".")
        config = self.config_data

        for key in keys[:-1]:
            config = config.setdefault(key, {})

        config[keys[-1]] = value
        self.logger.info(f"Clave configurada: {key_path} = {value}")

        # Guardar cambios en el archivo YAML
        self.save_config()

    def save_config(self):
        """
        Guarda los cambios en el archivo de configuración YAML.
        """
        try:
            with open(self.config_path, "w") as yaml_file:
                yaml.safe_dump(self.config_data, yaml_file)
            self.logger.info("Configuración guardada exitosamente.")
        except Exception as e:
            self.logger.error(f"Error al guardar la configuración: {e}")

    def clear_cache(self):
        """
        Limpia la caché interna y fuerza una recarga de las configuraciones.
        """
        self.config_data = {}
        self.load_config(self.config_path)
        self.logger.info("Caché de configuraciones limpiada y recargada desde el archivo.")

