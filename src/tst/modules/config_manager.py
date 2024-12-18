# config_manager.py - Clase para manejar la configuración del sistema desde un archivo YAML.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import yaml
import logging
import os
from modules.logging_manager import setup_logger

class ConfigManager:
    """
    Clase para manejar la configuración del sistema desde un archivo YAML.
    """

    def __init__(self, config_path, enable_validation=True):
        """
        Inicializa el ConfigManager cargando la configuración desde el archivo YAML.

        :param config_path: Ruta al archivo YAML.
        :param enable_validation: Habilita o deshabilita la validación de configuración al cargar.
        """
        self.config_path = config_path
        self.config = {}
        self.enable_validation = enable_validation

        # Configurar logger centralizado
        self.logger = setup_logger("[CONFIG_MANAGER]", {})

        self.default_config = {
            "system": {
                "enable_sensors": True,
                "enable_logging": True,
            },
            "network": {},
            "mux": {
                "i2c_address": 0x70
            },
            "sensors": {},
            "logging": {
                "log_file": "/home/raspberry-1/logs/pi1_logs.log",
                "error_log_file": "/home/raspberry-1/logs/pi1_error.log",
                "max_size_mb": 5,
                "backup_count": 3
            },
            "mqtt": {
                "broker": "localhost",
                "port": 1883,
                "topics": {
                    "sensor_data": "raspberry-1/sensor_data",
                    "alerts": "raspberry-1/alerts"
                }
            },
            "aws": {
                "region": "us-east-1",
                "iot_core_endpoint": "your_aws_iot_core_endpoint"
            }
        }
        self.load_config()

    def load_config(self):
        """
        Carga la configuración desde un archivo YAML. Si no existe, utiliza valores predeterminados.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as file:
                    self.config = yaml.safe_load(file)
                    # Convertir la dirección I2C si está en formato hexadecimal como string
                    if 'mux' in self.config and 'i2c_address' in self.config['mux']:
                        self.config['mux']['i2c_address'] = int(self.config['mux']['i2c_address'], 16) \
                            if isinstance(self.config['mux']['i2c_address'], str) else self.config['mux']['i2c_address']
                    self.logger.info(f"Configuración cargada desde {self.config_path}")
            else:
                self.logger.warning(f"El archivo de configuración no existe: {self.config_path}. Usando configuración predeterminada.")
                self.config = self.default_config

            # Validar configuración si está habilitado
            if self.enable_validation:
                self.validate_config()

        except yaml.YAMLError as e:
            self.logger.error(f"Error al leer el archivo YAML: {e}. Usando configuración predeterminada.")
            self.config = self.default_config
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            self.config = self.default_config

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

    def validate_config(self):
        """
        Valida las claves requeridas en la configuración y establece valores predeterminados si faltan.
        """
        for section, defaults in self.default_config.items():
            if section not in self.config:
                self.logger.warning(f"Sección {section} no encontrada en la configuración. Usando valores predeterminados.")
                self.config[section] = defaults
            else:
                for key, value in defaults.items():
                    if key not in self.config[section]:
                        self.logger.warning(f"Clave {key} no encontrada en {section}. Estableciendo valor predeterminado: {value}.")
                        self.config[section][key] = value
        self.save_config()

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
                return default
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
