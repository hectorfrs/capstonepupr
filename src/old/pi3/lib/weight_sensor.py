import smbus
import time

class WeightSensor:
    def __init__(self, i2c_bus=1, i2c_address=0x40, calibration_factor=2280):
        """
        Inicializa el sensor de peso.

        :param i2c_bus: Número del bus I2C donde está conectado el sensor.
        :param i2c_address: Dirección I2C del sensor de peso.
        :param calibration_factor: Factor de calibración para el sensor.
        """
        self.bus = smbus.SMBus(i2c_bus)
        self.i2c_address = i2c_address
        self.calibration_factor = calibration_factor
        self.offset = 0  # Offset para la tara

    def read_raw_data(self):
        """
        Lee los datos crudos del sensor de peso.

        :return: Valor crudo leído del sensor.
        """
        try:
            # Supongamos que el sensor devuelve 2 bytes de datos
            raw_data = self.bus.read_i2c_block_data(self.i2c_address, 0x00, 2)
            raw_value = (raw_data[0] << 8) | raw_data[1]
            print(f"Datos crudos del sensor de peso: {raw_value}")
            return raw_value
        except Exception as e:
            print(f"Error al leer datos del sensor de peso: {e}")
            return None

    def get_weight(self):
        """
        Obtiene el peso actual aplicando el factor de calibración y el offset de tara.

        :return: Peso calculado en unidades apropiadas (por ejemplo, gramos).
        """
        raw_value = self.read_raw_data()
        if raw_value is not None:
            weight = (raw_value - self.offset) / self.calibration_factor
            print(f"Peso calculado: {weight:.2f}")
            return weight
        else:
            return None

    def tare(self):
        """
        Realiza la tara del sensor de peso estableciendo el offset.
        """
        raw_value = self.read_raw_data()
        if raw_value is not None:
            self.offset = raw_value
            print(f"Tara realizada. Nuevo offset: {self.offset}")
        else:
            print("No se pudo realizar la tara. Lectura del sensor fallida.")

    def calibrate(self, known_weight):
        """
        Calibra el sensor de peso utilizando un peso conocido.

        :param known_weight: Peso conocido en las mismas unidades que se desean obtener.
        """
        raw_value = self.read_raw_data()
        if raw_value is not None:
            self.calibration_factor = (raw_value - self.offset) / known_weight
            print(f"Calibración completa. Nuevo factor de calibración: {self.calibration_factor}")
        else:
            print("No se pudo calibrar el sensor. Lectura del sensor fallida.")

# Ejemplo de uso:

# from lib.weight_sensor import WeightSensor

# # Cargar la configuración desde pi3_config.yaml
# import yaml
# config_path = 'config/pi3_config.yaml'
# with open(config_path, 'r') as file:
#     config = yaml.safe_load(file)

# sensor_config = config['weight_sensor']

# # Inicializar el sensor de peso
# weight_sensor = WeightSensor(
#     i2c_bus=1,
#     i2c_address=int(sensor_config['i2c_address'], 16),
#     calibration_factor=sensor_config['calibration_factor']
# )

# # Realizar tara
# weight_sensor.tare()

# # Calibrar el sensor con un peso conocido de 500 gramos
# known_weight = 500.0  # gramos
# weight_sensor.calibrate(known_weight)

# # Obtener el peso actual
# current_weight = weight_sensor.get_weight()
# if current_weight is not None:
#     print(f"Peso actual: {current_weight:.2f} gramos")
# else:
#     print("No se pudo obtener el peso actual.")
