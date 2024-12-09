# sensor_diagnostics.py - Módulo con funciones para ejecutar diagnósticos en los sensores conectados.
import logging
import time
from utils.alert_manager import AlertManager

def run_sensor_diagnostics(sensors, alert_manager=None):
    """
    Ejecuta diagnósticos en los sensores conectados.
    :param sensors: Lista de sensores inicializados.
    :param alert_manager: Manejador de alertas opcional.
    """
    diagnostics = {}
    for sensor in sensors:
        try:
            if sensor.is_connected():
                diagnostics[sensor.name] = {
                    "connected": True,
                    "temperature": sensor.read_temperature(),
                    "calibration_status": sensor.check_calibration(),
                    "gain_and_integration_valid": sensor.verify_integration_and_gain(
                        expected_gain=3, expected_time=100
                    ),
                    "spectral_data_valid": sensor.check_spectral_range(),
                }
                logging.info(f"Diagnósticos para {sensor.name}: {diagnostics[sensor.name]}")
            else:
                diagnostics[sensor.name] = {"connected": False}
                logging.warning(f"Sensor {sensor.name} no conectado.")
                if alert_manager:
                    alert_manager.send_alert("CRITICAL", f"Sensor {sensor.name} no conectado.", {})
        except Exception as e:
            diagnostics[sensor.name] = {"error": str(e)}
            logging.error(f"Error al diagnosticar el sensor {sensor.name}: {e}")
            if alert_manager:
                alert_manager.send_alert("CRITICAL", f"Error en {sensor.name}: {e}", {})
            if not self.sensors:
                logging.warning("No hay sensores inicializados para ejecutar diagnósticos.")
            return {}
        return diagnostics

