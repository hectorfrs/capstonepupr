import json
from datetime import datetime
import os
import yaml

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
