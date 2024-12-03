import qwiic_i2c
import logging
from utils.json_manager import generate_json, save_json


class PressureSensor:
    """
    Clase para manejar múltiples sensores de presión conectados al bus I2C.
    """

    def __init__(self, config, log_path="data/pressure_logs.json"):
        """
        Inicializa los sensores de presión basados en la configuración proporcionada.

        :param config: Diccionario de configuración del YAML.
        :param log_path: Ruta del archivo donde se guardarán los registros JSON.
        """
        self.i2c = qwiic_i2c.getI2CDriver()
        self.log_path = log_path

        # Configuración de sensores
        self.name = config.get("name", "Unnamed Sensor")
        self.i2c_address = config.get("i2c_address")
        self.min_pressure = config.get("min_pressure", 0.0)
        self.max_pressure = config.get("max_pressure", 25.0)

        # Verificar conexión del sensor
        if qwiic_i2c.isDeviceConnected(self.i2c_address):
            logging.info(f"Sensor de presión '{self.name}' conectado en la dirección {hex(self.i2c_address)}.")
        else:
            logging.error(f"Sensor de presión '{self.name}' no conectado en la dirección {hex(self.i2c_address)}.")
            raise ConnectionError(f"Sensor '{self.name}' no conectado.")

    def read_pressure(self):
        """
        Lee los datos de presión del sensor.

        :return: Valor de presión en PSI o None en caso de error.
        """
        try:
            # Leer 2 bytes desde el sensor
            raw_data = self.i2c.readBlock(self.i2c_address, 2)
            pressure = (raw_data[0] << 8) | raw_data[1]

            # Convertir los datos a PSI
            pressure_in_psi = self.convert_to_psi(pressure)

            # Verificar límites
            if not (self.min_pressure <= pressure_in_psi <= self.max_pressure):
                logging.warning(f"La presión del sensor '{self.name}' está fuera de rango: {pressure_in_psi} PSI.")

            logging.info(f"Lectura de presión del sensor '{self.name}': {pressure_in_psi} PSI.")
            self.log_pressure(pressure_in_psi)  # Guardar lectura en JSON
            return pressure_in_psi
        except Exception as e:
            logging.error(f"Error al leer la presión del sensor '{self.name}': {e}")
            return None

    def convert_to_psi(self, raw_data):
        """
        Convierte los datos en bruto del sensor a PSI.

        :param raw_data: Datos en bruto del sensor (16 bits).
        :return: Valor en PSI.
        """
        max_raw_value = 65535  # Máximo valor de 16 bits
        max_psi = 25           # Rango máximo en PSI del sensor
        return (raw_data / max_raw_value) * max_psi

    def log_pressure(self, pressure):
        """
        Genera un registro JSON para una lectura de presión.

        :param pressure: Valor de presión leído.
        """
        log = generate_json(
            sensor_id=self.name,
            pressure=pressure,
            valve_state=None,  # No aplica para lectura de sensores
            action="read_pressure",
            metadata={}
        )
        save_json(log, self.log_path)


class PressureSensorManager:
    """
    Clase para manejar múltiples sensores de presión.
    """

    def __init__(self, sensors_config, log_path="data/pressure_logs.json"):
        """
        Inicializa todos los sensores de presión.

        :param sensors_config: Lista de configuraciones de sensores.
        :param log_path: Ruta del archivo donde se guardarán los registros JSON.
        """
        self.sensors = []
        for sensor_config in sensors_config:
            try:
                sensor = PressureSensor(sensor_config, log_path)
                self.sensors.append(sensor)
            except ConnectionError as e:
                logging.warning(str(e))

    def read_all_sensors(self):
        """
        Lee los datos de presión de todos los sensores conectados.

        :return: Lista de lecturas de presión.
        """
        readings = []
        for sensor in self.sensors:
            reading = sensor.read_pressure()
            readings.append({"name": sensor.name, "pressure": reading})
        return readings
