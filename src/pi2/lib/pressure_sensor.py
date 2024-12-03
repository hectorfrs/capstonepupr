#import qwiic_micro_pressure
import qwiic_i2c
from utils.json_manager import generate_json, save_json

class PressureSensorManager:
    """
    Clase para manejar múltiples sensores de presión conectados al bus I2C.
    """
    def __init__(self, sensors, log_path="data/pressure_logs.json"):
        """
        Inicializa los sensores de presión.

        :param sensors: Lista de diccionarios con direcciones I2C y nombres de sensores.
        :param log_path: Ruta del archivo donde se guardarán los registros JSON.
        """
        self.sensors = []
        self.log_path = log_path

        for sensor in sensors:
            device = qwiic_micro_pressure.QwiicMicroPressureSensor(sensor["i2c_address"])
            if device.connected:
                self.sensors.append({"device": device, "name": sensor["name"]})
                device.begin()
                print(f"Pressure sensor '{sensor['name']}' connected at address {hex(sensor['i2c_address'])}.")
            else:
                print(f"Sensor at address {hex(sensor['i2c_address'])} not connected.")

    def read_all_sensors(self):
        """
        Lee los datos de presión de todos los sensores conectados.

        :return: Lista de lecturas de presión.
        """
        readings = []
        for sensor in self.sensors:
            try:
                pressure = sensor["device"].get_pressure()
                readings.append({"name": sensor["name"], "pressure": pressure})
                self.log_pressure(sensor["name"], pressure)  # Log JSON
            except Exception as e:
                print(f"Error reading sensor '{sensor['name']}': {e}")
                readings.append({"name": sensor["name"], "pressure": None})
        return readings

    def log_pressure(self, sensor_name, pressure):
        """
        Genera un registro JSON para una lectura de presión.

        :param sensor_name: Nombre del sensor.
        :param pressure: Valor de presión leído.
        """
        log = generate_json(
            sensor_id=sensor_name,
            pressure=pressure,
            valve_state=None,  # No aplica para lectura de sensores
            action="read_pressure",
            metadata={}
        )
        save_json(log, self.log_path)
