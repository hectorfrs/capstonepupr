# real_time_config.py - Clase para gestionar y monitorear cambios en el archivo de configuración.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import yaml
import os
import time
from threading import Thread
from modules.logging_manager import setup_logger  # Importa el logger centralizado

class RealTimeConfigManager:
    """
    Clase para gestionar y monitorear cambios en el archivo de configuración.
    """

    def __init__(self, config_path, reload_interval=5, logger_config=None):
        """
        Inicializa el gestor de configuración.

        :param config_path: Ruta al archivo de configuración YAML.
        :param reload_interval: Intervalo en segundos para verificar cambios en el archivo.
        :param logger_config: Configuración del logger.
        """
        if not isinstance(config_path, str):
            raise ValueError("config_path debe ser una cadena con la ruta del archivo de configuración.")

        self.config_path = config_path
        self.reload_interval = reload_interval
        self.last_modified_time = None
        self.config_data = {}
        self._stop_monitoring = False

        # Configurar logger específico para RealTimeConfig
        self.logger = setup_logger("[REALTIME]", logger_config or {})

        # Cargar configuración inicial
        self.load_config()

    def load_config(self):
        """
        Carga la configuración desde el archivo YAML.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as file:
                    self.config_data = yaml.safe_load(file)
                    self.last_modified_time = os.path.getmtime(self.config_path)
                    self.logger.info("Configuración cargada con éxito.")
            else:
                self.logger.error(f"El archivo de configuración no existe: {self.config_path}")
        except yaml.YAMLError as e:
            self.logger.error(f"Error al leer el archivo YAML: {e}")
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")

    def save_config(self):
        """
        Guarda la configuración actualizada en el archivo YAML.
        """
        try:
            with open(self.config_path, 'w') as file:
                yaml.safe_dump(self.config_data, file)
            self.last_modified_time = os.path.getmtime(self.config_path)
            self.logger.info("Configuración guardada con éxito.")
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {e}")

    def delete_key(self, section, key):
        """
        Elimina una clave de una sección en la configuración.

        :param section: Sección del archivo YAML.
        :param key: Clave a eliminar.
        """
        if section in self.config_data and key in self.config_data[section]:
            del self.config_data[section][key]
            self.save_config()
            self.logger.info(f"Clave {key} eliminada de la sección {section}.")
        else:
            self.logger.warning(f"No se encontró la clave {key} en la sección {section}.")

    def monitor_config(self):
        """
        Monitorea el archivo de configuración y recarga cambios si es necesario.
        """
        self.logger.info("Iniciando monitoreo del archivo de configuración.")
        while not self._stop_monitoring:
            try:
                if os.path.exists(self.config_path):
                    current_modified_time = os.path.getmtime(self.config_path)
                    if current_modified_time != self.last_modified_time:
                        self.logger.info("Cambio detectado en el archivo de configuración. Recargando...")
                        self.load_config()
                else:
                    self.logger.error(f"El archivo de configuración no existe: {self.config_path}")
            except Exception as e:
                self.logger.error(f"Error monitoreando configuración: {e}")
            time.sleep(self.reload_interval)

    def get_config(self):
        """
        Devuelve los datos de configuración actuales.
        """
        return self.config_data

    def start_monitoring(self):
        """
        Inicia el monitoreo del archivo de configuración en un hilo separado.
        """
        self._stop_monitoring = False
        self.monitor_thread = Thread(target=self.monitor_config, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """
        Detiene el monitoreo del archivo de configuración.
        """
        self._stop_monitoring = True
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join()
        self.logger.info("Monitoreo del archivo de configuración detenido.")

    def set_value(self, section, key, value):
        """
        Actualiza un valor en la configuración y guarda el archivo YAML.

        :param section: Sección del archivo YAML.
        :param key: Clave dentro de la sección.
        :param value: Valor a establecer.
        """
        if section not in self.config_data:
            self.config_data[section] = {}
        self.config_data[section][key] = value
        self.save_config()
