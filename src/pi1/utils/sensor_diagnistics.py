# sensor_diagnostics.py
import logging

def run_sensor_diagnostics(sensors):
    """
    Ejecuta diagnósticos en los sensores conectados.
    """
    for sensor in sensors:
        try:
            if sensor.is_connected():
                logging.info(f"Sensor {sensor.name} conectado correctamente.")
                # Agregar lecturas adicionales de diagnóstico si es posible
                temp = sensor.read_temperature()
                logging.info(f"Temperatura del sensor {sensor.name}: {temp}°C")
            else:
                logging.warning(f"Sensor {sensor.name} no está conectado.")
        except Exception as e:
            logging.error(f"Error al diagnosticar el sensor {sensor.name}: {e}")
