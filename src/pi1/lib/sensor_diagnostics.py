# sensor_diagnostics.py - Módulo con funciones para ejecutar diagnósticos en los sensores conectados.
import logging
import time
from utils.alert_manager import AlertManager

def run_sensor_diagnostics(sensors, alert_manager=None):
    """
    Ejecuta diagnósticos en los sensores conectados.
    :param sensors: Lista de sensores inicializados.
    :param alert_manager: Manejador de alertas opcional.
    :return: Diccionario con los resultados del diagnóstico.
    """
    diagnostics = {}
    if not sensors:
        logging.warning("No hay sensores inicializados para ejecutar diagnósticos.")
        return diagnostics  # Retorna un diccionario vacío

    for sensor in sensors:
        try:
            if sensor.is_connected():
                diagnostics[sensor.name] = {
                    "status": "OK",
                    "temperature": sensor.read_temperature(),
                }
                logging.info(f"Sensor {sensor.name} conectado y operativo.")
            else:
                diagnostics[sensor.name] = {"status": "NOT_CONNECTED"}
                logging.warning(f"Sensor {sensor.name} no conectado.")
                if alert_manager:
                    alert_manager.send_alert("CRITICAL", f"Sensor {sensor.name} no conectado.", {})
        except Exception as e:
            diagnostics[sensor.name] = {"status": "ERROR", "error": str(e)}
            logging.error(f"Error diagnosticando el sensor {sensor.name}: {e}")
            if alert_manager:
                alert_manager.send_alert("CRITICAL", f"Error en {sensor.name}: {e}", {})
    return diagnostics



