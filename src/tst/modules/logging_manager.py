# logging_manager.py - Módulo para configurar y gestionar los logs de la aplicación.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(module_name, config):
    """
    Configura y devuelve un logger para un módulo específico.

    :param module_name: Nombre del módulo (__name__).
    :param config: Configuración para el logger global.
    :return: Instancia de logger configurado.
    """
    logger = logging.getLogger(module_name)

    # Evitar configurar múltiples veces el mismo logger
    if logger.hasHandlers():
        return logger

    enable_debug = config.get('enable_debug', False)
    logger.setLevel(logging.DEBUG if enable_debug else logging.INFO)

    # Formato del log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    # Configurar archivo de log rotativo
    log_file = os.path.expanduser(config.get('log_file', 'logs/app.log'))
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)

    max_log_size = config.get('max_size_mb', 5) * 1024 * 1024
    backup_count = config.get('backup_count', 3)

    file_handler = RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=backup_count)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Configurar salida de consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Configurar archivo para errores
    error_log_file = os.path.expanduser(config.get('error_log_file', 'logs/error.log'))
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger

def initialize_global_logging(config):
    """
    Inicializa los loggers globales para los módulos.

    :param config: Configuración para el logging global.
    """
    global_config = config.get('logging', {})
    modules = config.get('modules', [])

    for module in modules:
        setup_logger(module, global_config)

# Ejemplo de configuración en YAML cargada en runtime
# config = {
#     'logging': {
#         'log_file': '/path/to/logs/app.log',
#         'error_log_file': '/path/to/logs/error.log',
#         'max_size_mb': 10,
#         'backup_count': 5,
#         'enable_debug': True
#     },
#     'modules': ['modules.mqtt_handler', 'modules.network_manager']
# }

# initialize_global_logging(config)
