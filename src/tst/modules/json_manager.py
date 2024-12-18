# json_manager.py - Manejo centralizado de datos JSON para almacenamiento y recuperación.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

import json
import os
from datetime import datetime
from modules.logging_manager import setup_logger

# Configurar logger centralizado
logger = setup_logger("[JSON_MANAGER]", {})

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
    logger.info("Generando JSON con los datos de medición.")
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
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Crear el directorio si no existe
        with open(file_path, "a") as file:  # Modo 'a' para agregar al archivo existente
            file.write(json.dumps(data) + "\n")
        logger.info(f"Datos guardados en {file_path}.")
    except Exception as e:
        logger.error(f"Error guardando datos en {file_path}: {e}")

def load_json(file_path):
    """
    Carga datos JSON desde un archivo.

    :param file_path: Ruta del archivo a cargar.
    :return: Lista de objetos JSON.
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"El archivo {file_path} no existe.")
            return []
        with open(file_path, "r") as file:
            logger.info(f"Cargando datos desde {file_path}.")
            return [json.loads(line) for line in file.readlines()]
    except Exception as e:
        logger.error(f"Error cargando datos desde {file_path}: {e}")
        return []

def clean_json(file_path):
    """
    Limpia el contenido de un archivo JSON.

    :param file_path: Ruta del archivo JSON a limpiar.
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, "w") as file:
                file.truncate(0)
            logger.info(f"El archivo {file_path} ha sido limpiado.")
        else:
            logger.warning(f"El archivo {file_path} no existe.")
    except Exception as e:
        logger.error(f"Error limpiando el archivo {file_path}: {e}")
