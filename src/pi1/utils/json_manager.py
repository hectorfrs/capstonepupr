import json
import os
from datetime import datetime


def generate_json(sensor_id, channel, spectral_data, detected_material, confidence):
    """
    Genera un objeto JSON para representar los datos de medición.

    :param sensor_id: ID del sensor que tomó la medición.
    :param channel: Canal del MUX correspondiente.
    :param spectral_data: Diccionario con valores espectrales.
    :param detected_material: Material identificado.
    :param confidence: Nivel de confianza en la clasificación.
    :return: Diccionario JSON.
    """
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "sensor_id": sensor_id,
        "channel": channel,
        "spectral_data": spectral_data,
        "detected_material": detected_material,
        "confidence": confidence
    }


def save_json(data, file_path):
    """
    Guarda un objeto JSON en un archivo.

    :param data: Objeto JSON a guardar.
    :param file_path: Ruta del archivo donde guardar los datos.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Crear el directorio si no existe
    with open(file_path, "a") as file:  # Modo 'a' para agregar al archivo existente
        file.write(json.dumps(data) + "\n")
    print(f"Datos guardados en {file_path}")


def load_json(file_path):
    """
    Carga datos JSON desde un archivo.

    :param file_path: Ruta del archivo a cargar.
    :return: Lista de objetos JSON.
    """
    if not os.path.exists(file_path):
        print(f"El archivo {file_path} no existe.")
        return []
    with open(file_path, "r") as file:
        return [json.loads(line) for line in file.readlines()]


def clean_json(file_path):
    """
    Limpia el contenido de un archivo JSON.

    :param file_path: Ruta del archivo JSON a limpiar.
    """
    if os.path.exists(file_path):
        with open(file_path, "w") as file:
            file.truncate(0)
        print(f"El archivo {file_path} ha sido limpiado.")
    else:
        print(f"El archivo {file_path} no existe.")
