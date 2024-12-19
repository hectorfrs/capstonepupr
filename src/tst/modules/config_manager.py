# config_manager.py - Manejador de configuraciones centralizadas para el proyecto
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import yaml
import logging
import os

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
        self.config_data = None

        # Configurar logger
        try:
            self.logger = self.setup_logger()
        except Exception as e:
            self.logger = logging.getLogger("[CONFIG_MANAGER]")
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            self.logger.warning(f"Usando logger de fallback debido a errores en LoggingManager: {e}")

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


    def setup_logger(self):
        """
        Configura un logger centralizado para ConfigManager.

        :return: Instancia del logger configurado.
        """
        logger = logging.getLogger("[CONFIG_MANAGER]")
        logger.setLevel(logging.DEBUG)

        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(fmt=log_format, datefmt="%Y-%m-%d %H:%M:%S.%f")

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

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

