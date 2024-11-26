import smbus
import time

class PressureSensor:
    def __init__(self, i2c_bus=1, min_pressure=0.0, max_pressure=25.0):
        """
        Inicializa el controlador de múltiples sensores de presión.

        :param i2c_bus: Número del bus I2C donde están conectados los sensores.
        :param min_pressure: Presión mínima en PSI.
        :param max_pressure: Presión máxima en PSI.
        """
        self.bus = smbus.SMBus(i2c_bus)
        self.min_pressure = min_pressure
        self.max_pressure = max_pressure

    def read_raw_data(self, i2c_address):
        """
        Lee los datos crudos de un sensor específico.

        :param i2c_address: Dirección I2C del sensor.
        :return: Datos crudos leídos del sensor.
        """
        try:
            print(f"Leyendo datos del sensor en la dirección I2C {hex(i2c_address)}...")
            raw_data = self.bus.read_i2c_block_data(i2c_address, 0x00, 2)
            print(f"Datos crudos: {raw_data}")
            return raw_data
        except Exception as e:
            print(f"Error al leer datos del sensor {hex(i2c_address)}: {e}")
            return None

    def calculate_pressure(self, raw_data):
        """
        Convierte los datos crudos en valores de presión en PSI.

        :param raw_data: Datos crudos leídos del sensor.
        :return: Presión en PSI.
        """
        if raw_data is None or len(raw_data) != 2:
            print("Datos crudos inválidos para el cálculo de presión.")
            return None

        raw_value = (raw_data[0] << 8) | raw_data[1]
        pressure = ((raw_value - 1638) * (self.max_pressure - self.min_pressure)) / (14745 - 1638) + self.min_pressure
        print(f"Presión calculada: {pressure:.2f} PSI")
        return pressure

    def read_all_sensors(self, sensors):
        """
        Lee y calcula la presión de todos los sensores configurados.

        :param sensors: Lista de sensores con sus direcciones I2C y nombres.
        :return: Diccionario con los valores de presión de cada sensor.
        """
        pressures = {}
        for sensor in sensors:
            raw_data = self.read_raw_data(sensor['i2c_address'])
            pressure = self.calculate_pressure(raw_data)
            if pressure is not None:
                pressures[sensor['name']] = pressure
        return pressures

# Ejemplo de Uso:

# from lib.pressure_sensor import PressureSensor

# # Supongamos que tenemos la configuración de sensores de pi2_config.yaml
# sensors_config = [
#     {'i2c_address': 0x28, 'name': 'valve_1_inlet'},
#     {'i2c_address': 0x29, 'name': 'valve_1_outlet'},
#     {'i2c_address': 0x2A, 'name': 'valve_2_inlet'},
#     {'i2c_address': 0x2B, 'name': 'valve_2_outlet'},
# ]

# # Inicializar el controlador de sensores
# pressure_sensor = PressureSensor(i2c_bus=1, min_pressure=0.0, max_pressure=25.0)

# # Leer las presiones de todos los sensores
# pressures = pressure_sensor.read_all_sensors(sensors_config)
# print("Lecturas de presión:", pressures)
