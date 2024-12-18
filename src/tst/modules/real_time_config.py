#real_time_config.py - Clase para gestionar y monitorear cambios en el archivo de configuración.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import yaml
import os
import time
import logging
from threading import Thread


class RealTimeConfigManager:
    """
    Clase para gestionar y monitorear cambios en el archivo de configuración.
    """
    def __init__(self, config_path, reload_interval=5):
        """
        Inicializa el gestor de configuración.

        :param config_path: Ruta al archivo de configuración YAML.
        :param reload_interval: Intervalo en segundos para verificar cambios en el archivo.
        """
        self.config_path = config_path
        self.reload_interval = reload_interval
        self.last_modified_time = None
        self.config_data = {}
        self._stop_monitoring = False

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
                    logging.info("[REALTIME] [CONFIG] Configuración cargada con éxito.")
                    if "log_file" not in self.config_data.get("logging", {}):
                        logging.warning("[REALTIME] [CONFIG] Clave 'log_file' no encontrada. Usando valor predeterminado.")
                        self.config_data["logging"]["log_file"] = "/home/raspberry-1/logs/default.log"
            else:
                logging.error(f"[REALTIME] [CONFIG] El archivo de configuración no existe: {self.config_path}")
        except Exception as e:
            logging.error(f"[REALTIME] [CONFIG] Error cargando configuración: {e}")

    def save_config(self):
        """
        Guarda la configuración actualizada en el archivo YAML.
        """
        try:
            with open(self.config_path, 'w') as file:
                yaml.safe_dump(self.config_data, file)
            self.last_modified_time = os.path.getmtime(self.config_path)
            logging.info("[REALTIME] [CONFIG] Configuración guardada con éxito.")
        except Exception as e:
            logging.error(f"[REALTIME] [CONFIG] Error guardando configuración: {e}")

    def delete_key(self, section, key):
        """
        Elimina una clave de una sección en la configuración.

        :param section: Sección del archivo YAML.
        :param key: Clave a eliminar.
        """
        if section in self.config_data and key in self.config_data[section]:
            del self.config_data[section][key]
            self.save_config()
            logging.info(f"[REALTIME] [CONFIG] Clave {key} eliminada de la sección {section}.")
        else:
            logging.warning(f"[REALTIME] [CONFIG] No se encontró la clave {key} en la sección {section}.")

    def monitor_config(self):
        """
        Monitorea el archivo de configuración y recarga cambios si es necesario.
        """
        logging.info("[REALTIME] [CONFIG] Iniciando monitoreo del archivo de configuración.")
        while not self._stop_monitoring:
            try:
                current_modified_time = os.path.getmtime(self.config_path)
                if current_modified_time != self.last_modified_time:
                    logging.info("[REALTIME] [CONFIG] Cambio detectado en el archivo de configuración. Recargando...")
                    self.load_config()
            except Exception as e:
                logging.error(f"[REALTIME] [CONFIG] Error monitoreando configuración: {e}")
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
        if self.monitor_thread.is_alive():
            self.monitor_thread.join()
        logging.info("[REALTIME] [CONFIG] Monitoreo del archivo de configuración detenido.")
    
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

    


