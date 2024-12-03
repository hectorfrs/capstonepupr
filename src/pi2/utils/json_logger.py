import json
import os
import yaml
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

def log_detection(data, config_path="config/config.yaml"):
    """
    Registra datos en un archivo JSON, agregando un timestamp.
    La ruta del archivo de log se define en config.yaml.

    :param data: Diccionario con los datos a registrar.
    :param config_path: Ruta al archivo de configuración YAML.
    """
    # Cargar configuración desde config.yaml
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Obtener la ruta del archivo de log desde la configuración
    file_path = config.get("logging", {}).get("log_file", "logs/default_log.json")
    
    # Agregar timestamp al registro
    data["timestamp"] = datetime.now().isoformat()
    
    # Crear el directorio si no existe
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Escribir datos en el archivo JSON
    with open(file_path, "a") as f:
        f.write(json.dumps(data) + "\n")
    
    print(f"Datos guardados en {file_path}: {data}")



def configure_logging(config):
    """
    Configura el logging según los parámetros definidos en config.yaml.

    :param config: Diccionario con la configuración de logs desde config.yaml.
    """
    max_log_size = config.get("logging", {}).get("max_size_mb", 5) * 1024 * 1024
    backup_count = config.get("logging", {}).get("backup_count", 3)

    # Configuración del formato de los logs
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

    # Crear directorio de logs si no existe
    log_file = os.path.expanduser(config['logging']['log_file'])
    log_dir = os.path.dirname(log_file)

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configurar manejador principal con rotación
    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=max_log_size,
        backupCount=backup_count,
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # Configurar logger global
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger
