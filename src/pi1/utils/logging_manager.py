import yaml
import time
import sys
import os
import logging
from logging.handlers import RotatingFileHandler

class LoggingManager:

    def configure_logging(config):
        """
        Configura el sistema de logging.
        """
        log_file = os.path.expanduser(config['logging']['log_file'])
        log_dir = os.path.dirname(log_file)
        error_log_file = config['logging']['error_log_file']
        max_log_size = config.get("logging", {}).get("max_size_mb", 5) * 1024 * 1024
        backup_count = config.get("logging", {}).get("backup_count", 3)

        # Crear directorio de logs si no existe
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Configuración del logger principal
        logger = logging.getLogger()
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

        # Manejador de errores
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)

        logging.info("Sistema de logging configurado correctamente.")