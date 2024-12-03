import qwiic_i2c
from utils.json_manager import generate_json, save_json
import yaml


class PressureSensor:
    """
    Clase para manejar múltiples sensores de presión conectados al bus I2C.
    """

    def __init__(self, config_path="/home/raspberry-2/capstonepupr/src/pi2/config/pi2_config.yaml", log_path="data/pressure_logs.json"):
        """
        Inicializa los sensores de presión basados en la configuración del YAML.

        :param config_path: Ruta al archivo de configuración YAML.
        :param log_path: Ruta del archivo donde se guardarán los registros JSON.
        """
        self.i2c = qwiic_i2c.getI2CDriver()
        self.log_path = log_path

        # Cargar configuración desde el archivo YAML
        self.config = self.load_config(config_path)
        self.sensors = self.config["pressure_sensors"]["sensors"]
        self.min_pressure = self.config["pressure_sensors"]["min_pressure"]
        self.max_pressure = self.config["pressure_sensors"]["max_pressure"]

        # Inicializar sensores
        self.connected_sensors = []
        for sensor in self.sensors:
            if qwiic_i2c.isDeviceConnected(sensor["i2c_address"]):
                self.connected_sensors.append({"address": sensor["i2c_address"], "name": sensor["name"]})
                print(f"Sensor de presión '{sensor['name']}' conectado en la dirección {hex(sensor['i2c_address'])}.")
            else:
                print(f"Sensor en la dirección {hex(sensor['i2c_address'])} no está conectado.")

    @staticmethod
    def load_config(config_path):
        """
        Carga la configuración desde un archivo YAML.

        :param config_path: Ruta al archivo YAML.
        :return: Diccionario con la configuración cargada.
        """
        with open(config_path, "r") as file:
            return yaml.safe_load(file)

    def read_all_sensors(self):
        """
        Lee los datos de presión de todos los sensores conectados.

        :return: Lista de lecturas de presión.
        """
        readings = []
        for sensor in self.connected_sensors:
            try:
                # Leer 2 bytes desde el sensor
                raw_data = self.i2c.readBlock(sensor["address"], 2)
                pressure = (raw_data[0] << 8) | raw_data[1]

                # Normalizar la presión a PSI si está en rango
                pressure_in_psi = self.convert_to_psi(pressure)

                # Verificar límites de presión
                if not (self.min_pressure <= pressure_in_psi <= self.max_pressure):
                    print(f"Advertencia: La presión del sensor '{sensor['name']}' está fuera de rango.")

                # Agregar a las lecturas
                readings.append({"name": sensor["name"], "pressure": pressure_in_psi})
                self.log_pressure(sensor["name"], pressure_in_psi)  # Guardar en JSON
            except Exception as e:
                print(f"Error leyendo el sensor '{sensor['name']}': {e}")
                readings.append({"name": sensor["name"], "pressure": None})
        return readings

    def convert_to_psi(self, raw_data):
        """
        Convierte los datos en bruto del sensor a PSI.

        :param raw_data: Datos en bruto del sensor (16 bits).
        :return: Valor en PSI.
        """
        max_raw_value = 65535  # Máximo valor de 16 bits
        max_psi = 25           # Rango máximo en PSI del sensor
        return (raw_data / max_raw_value) * max_psi

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


# # Ejemplo de uso
# if __name__ == "__main__":
#     manager = PressureSensorManager(config_path="config/pi2_config.yaml")
#     readings = manager.read_all_sensors()
#     for reading in readings:
#         print(f"Sensor: {reading['name']}, Pressure: {reading['pressure']} PSI")
