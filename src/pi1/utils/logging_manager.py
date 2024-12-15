# logging_manager.py - Clase para gestionar el sistema de logging y monitoreo de funciones.
# logging_manager.py - Class FunctionMonitor - Monitor de funciones y sistema de logging.   
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024

import os
import time
import socket
import yaml
import logging
from threading import Thread
from logging.handlers import RotatingFileHandler


class FunctionMonitor:
    def __init__(self, config_path, log_file="/var/log/centralized.log", mqtt_config=None,mqtt_publisher=None, reload_interval=5):
        """
        Inicializa el monitor de funciones.

        :param config_path: Ruta al archivo de configuración YAML.
        :param log_file: Ruta del archivo de log.
        :param mqtt_config: Configuración MQTT (broker, port, topic, etc.).
        :param reload_interval: Intervalo en segundos para verificar cambios en el archivo.
        """
        self.config_path = config_path
        self.reload_interval = reload_interval
        self.last_config = {}
        self.stop_monitor = False
        self.mqtt_publisher = mqtt_publisher

        self.logger = None  # El logger se inicializará al cargar la configuración

        initial_config = self._load_config()
        if initial_config:
            self.logger = self._setup_logger(initial_config)
            self.config = initial_config  # Guarda la configuración en self.config

            # Configurar MQTT si está habilitado
            if self.config.get("mqtt"):
                self._setup_mqtt()

    def _setup_logger(self, config):
        """
        Configura el sistema de logging.

        :param config: Configuración cargada desde el archivo YAML.
        :return: Instancia del logger configurado.
        """
        log_file = os.path.expanduser(config['logging']['log_file'])
        log_dir = os.path.dirname(log_file)
        error_log_file = os.path.expanduser(config['logging']['error_log_file'])
        max_log_size = config.get("logging", {}).get("max_size_mb", 5) * 1024 * 1024
        backup_count = config.get("logging", {}).get("backup_count", 3)

        # Crear directorio de logs si no existe
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Configuración del logger principal
        logger = logging.getLogger("FunctionMonitor")
        logger.setLevel(logging.DEBUG if config.get('system', {}).get('enable_detailed_logging', False) else logging.INFO)

        # Formato de los logs
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"

        # Manejador de archivo (RotatingFileHandler)
        file_handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=backup_count)
        file_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
        file_handler.setLevel(logging.DEBUG if config.get('system', {}).get('enable_detailed_logging', False) else logging.INFO)
        logger.addHandler(file_handler)

        # Manejador de consola (StreamHandler)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
        console_handler.setLevel(logging.DEBUG if config.get('system', {}).get('enable_detailed_logging', False) else logging.INFO)
        logger.addHandler(console_handler)

        # Manejador de errores (FileHandler)
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)

        return logger

    def _setup_mqtt(self):
        """
        Configura y conecta el cliente MQTT.
        """
        from utils.mqtt_publisher import MQTTPublisher
        try:
            mqtt_config = self.config.get("mqtt", {})
            required_keys = ["broker_address", "port", "topics"]
            for key in required_keys:
                if key not in mqtt_config:
                    raise KeyError(f"Clave MQTT faltante: {key}")

            self.mqtt_publisher = MQTTPublisher({
                "broker_address": mqtt_config["broker_address"],
                "port": mqtt_config["port"],
                "username": mqtt_config.get("username"),
                "password": mqtt_config.get("password"),
                "topics": mqtt_config["topics"]
            }, local=True)
            self.mqtt_publisher.connect()
            self.logger.info("[MONITOR] [LOG] Cliente MQTT configurado y conectado.")

        except Exception as e:
            self.logger.error(f"[MONITOR] [LOG] Error configurando MQTT: {e}")


    def _load_config(self):
        """
        Carga el archivo de configuración YAML.
        """
        try:
            with open(self.config_path, "r") as file:
                config = yaml.safe_load(file) or {}
                if "system" not in config:
                    raise ValueError("[MONITOR] [LOG] Key 'system' no encontrada en configuración YAML.")
                return config
        except Exception as e:
            if self.logger:
                self.logger.error(f"[MONITOR] [LOG] Error cargando configuración: {e}")
            return {}

    def _document_change(self, function, status):
        message = f"[MONITOR] [LOG] [{socket.gethostname()}] Funcionalidad: {function}, Estado: {'Activado' if status else 'Desactivado'}"
        self.logger.info(message)

        # Publicar solo una vez la configuración de MQTT al iniciar
        if not hasattr(self, '_mqtt_config_logged'):
            self.logger.debug(f"[MONITOR] [LOG] Configuración de MQTT: {self.config['mqtt']}")
            setattr(self, '_mqtt_config_logged', True)

        if self.mqtt_publisher:
            try:
                topic = self.config['mqtt']['topics'].get('functions')
                if not topic:
                    raise KeyError("[MONITOR] [LOG] Tópico 'functions' no configurado en MQTT.")
                self.mqtt_handler.publish(topic, message)
                time.sleep(0.2)
            except KeyError as e:
                self.logger.error(f"[MONITOR] [LOG] Error: {e}")
            except Exception as e:
                self.logger.error(f"[MONITOR] [LOG] Error publicando mensaje en MQTT: {e}")


    
    def monitor_changes(self):
        """
        Monitorea cambios en el archivo de configuración.
        """
        self.logger.info("[MONITOR] [LOG] Iniciando monitoreo de funciones.")
        while not self.stop_monitor:
            current_config = self._load_config()
            if not current_config:
                time.sleep(self.reload_interval)
                continue

            # Detectar cambios en las funcionalidades
            for function, status in current_config.get("system", {}).items():
                if self.last_config.get(function) != status:
                    self._document_change(function, status)

            self.last_config = current_config.get("system", {})
            time.sleep(self.reload_interval)

    def start(self):
        """
        Inicia el monitoreo en un hilo separado.
        """
        monitor_thread = Thread(target=self.monitor_changes, daemon=True)
        monitor_thread.start()

    def stop(self):
        """Detiene el monitoreo."""
        self.logger.info("[MONITOR] [LOG] Deteniendo monitoreo de funciones.")
        self.stop_monitor = True
