# logging_manager.py - Clase para gestionar el sistema de logging y monitoreo de funciones.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


class CustomFormatter(logging.Formatter):
    """
    Formatea los logs incluyendo milisegundos con precisión utilizando datetime.
    """

    converter = datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        """
        Sobrescribe el método para formatear la hora utilizando datetime.
        """
        ct = self.converter(record.created)
        if datefmt:
            return ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = f"{t}.{int(record.msecs):03d}"
            return s

class LoggingManager:
    """
    Clase para configurar loggers centralizados y rotativos para diferentes módulos del sistema.
    """

    def __init__(self, config_manager):
        """
        Inicializa el manejador de logging con configuraciones centralizadas.

        :param config_manager: Instancia de ConfigManager para manejar configuraciones dinámicas.
        """
        self.config_manager = config_manager

    def setup_logger(self, module_name):
        """
        Configura y devuelve un logger para un módulo específico.

        :param module_name: Nombre del módulo (__name__).
        :return: Instancia de logger configurado.
        """
        logger = logging.getLogger(module_name)

        # Configurar nivel de log
        enable_debug = self.config_manager.get('logging.enable_debug', False)
        logger.setLevel(logging.DEBUG if enable_debug else logging.INFO)

        # Evitar configurar múltiples veces el mismo logger
        if logger.hasHandlers():
            return logger
        
        # Formato del log
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        formatter = CustomFormatter(fmt=log_format, datefmt=date_format)

        # Configurar archivo de log rotativo
        log_file = os.path.expanduser(self.config_manager.get('logging.log_file', 'logs/app.log'))
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)

        max_log_size = self.config_manager.get('logging.max_size_mb', 5) * 1024 * 1024
        backup_count = self.config_manager.get('logging.backup_count', 3)

        file_handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=backup_count)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Configurar salida de consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Configurar archivo para errores
        error_log_file = os.path.expanduser(self.config_manager.get('logging.error_log_file', 'logs/error.log'))
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

        return logger