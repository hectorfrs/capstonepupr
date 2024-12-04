# sensor_diagnostics.py
import logging
import time
from utils.alert_manager import AlertManager

def run_sensor_diagnostics(sensors, alert_manager=None):
    """
    Ejecuta diagnósticos en los sensores conectados.
    """
    for sensor in sensors:
        try:
            start_time = time.time()
            if sensor.is_connected():
                logging.info(f"Sensor {sensor.name} conectado correctamente.")
                # Agregar lecturas adicionales de diagnóstico
                temp = sensor.read_temperature()
                logging.info(f"Temperatura del sensor {sensor.name}: {temp}°C")
                response_time = time.time() - start_time
                logging.info(f"Tiempo de respuesta del sensor {sensor.name}: {response_time:.2f} ms")
            else:
                message = f"Sensor {sensor.name} no está conectado."
                logging.warning(message)
                if alert_manager:
                    alert_manager.send_alert("CRITICAL", message, {"sensor": sensor.name})
        except Exception as e:
            message = f"Error al diagnosticar el sensor {sensor.name}: {e}"
            logging.error(message)
            if alert_manager:
                alert_manager.send_alert("CRITICAL", message, {"sensor": sensor.name})
