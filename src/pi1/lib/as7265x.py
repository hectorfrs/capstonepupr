from smbus2 import SMBus
from lib.spectrometer import Spectrometer
import yaml


class CustomAS7265x(Spectrometer):
    """
    Clase extendida para interactuar con el sensor AS7265x.
    Combina configuraciones avanzadas y funciones simplificadas para lecturas espectroscópicas.
    """

    def __init__(self, config_path="config/pi1_config.yaml"):
        """
        Inicializa el sensor AS7265x usando valores de configuración YAML.

        :param config_path: Ruta al archivo de configuración YAML.
        """
        # Cargar configuración desde YAML
        self.config = self.load_config(config_path)

        # Extraer parámetros del sensor
        self.i2c_bus = self.config['sensors']['as7265x']['i2c_bus']
        self.i2c_address = 0x49  # Dirección predeterminada del sensor
        self.integration_time = self.config['sensors']['as7265x']['integration_time']
        self.gain = self.config['sensors']['as7265x']['gain']

        # Inicializar el bus I²C
        self.bus = SMBus(self.i2c_bus)

        # Inicializar la biblioteca SparkFun
        #super().__init__(self.bus)
        # Llama al constructor de la clase base con el número de bus I2C
        super().__init__(i2c_bus=self.config['sensors']['as7265x']['i2c_bus'])


        # Configurar el sensor
        self.configure_sensor()

    @staticmethod
    def load_config(config_path):
        """
        Carga la configuración desde un archivo YAML.

        :param config_path: Ruta al archivo YAML.
        :return: Diccionario con la configuración cargada.
        """
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    

    def configure_sensor(self):
        """
        Configura el sensor AS7265x con el tiempo de integración y ganancia especificados.
        """
        if not self.is_connected():
            print(f"Sensor no detectado en {hex(self.i2c_address)}. Saltando configuración.")
            return

        try:
            self.set_integration_time(self.integration_time)
            print(f"Tiempo de integración configurado: {self.integration_time}")
        except Exception as e:
            print(f"Error configurando el sensor: {e}")
            raise

        print(f"Configurando el sensor AS7265x en la dirección {hex(self.i2c_address)}...")
        self.set_integration_time(self.integration_time)
        self.set_gain(self.gain)
        print("Configuración del sensor completada.")

    def read_data(self):
        """
        Simula la lectura de datos del sensor.
        """
        if not self.is_connected():
            print("El sensor no está conectado. No se pueden leer datos.")
            return {}

    def set_integration_time(self, time_ms):
        """
        Establece el tiempo de integración del sensor.

        :param time_ms: Tiempo de integración en milisegundos (0-255 ms).
        """
        register_value = int(time_ms / 2.8)  # Conversión según la documentación
        self.write_register(0x04, register_value)
        print(f"Tiempo de integración configurado: {time_ms} ms.")

    def set_gain(self, gain_level):
        """
        Establece la ganancia del sensor.

        :param gain_level: Nivel de ganancia (0: 1x, 1: 3.7x, 2: 16x, 3: 64x).
        """
        if gain_level < 0 or gain_level > 3:
            raise ValueError("El nivel de ganancia debe estar entre 0 y 3.")
        self.write_register(0x05, gain_level)
        print(f"Ganancia configurada: {gain_level}x.")

    def write_register(self, register, value):
        """
        Escribe un valor en un registro del sensor.

        :param register: Registro a escribir.
        :param value: Valor a escribir.
        """
        self.bus.write_byte_data(self.i2c_address, register, value)
        print(f"Escribiendo {value} en el registro {hex(register)}.")

    def read_register(self, register):
        """
        Lee un valor de un registro del sensor.

        :param register: Registro a leer.
        :return: Valor leído.
        """
        value = self.bus.read_byte_data(self.i2c_address, register)
        print(f"Valor leído del registro {hex(register)}: {value}")
        return value

    def read_calibrated_spectrum(self):
        """
        Lee los datos calibrados del espectro usando la biblioteca SparkFun.

        :return: Diccionario con valores espectrales calibrados.
        """
        print("Leyendo datos calibrados del espectro...")
        calibrated_values = super().get_calibrated_values()
        print(f"Espectro calibrado: {calibrated_values}")
        return calibrated_values

    def read_advanced_spectrum(self):
        """
        Lee los datos espectrales directamente desde registros.

        :return: Diccionario con valores espectrales.
        """
        print("Leyendo datos espectrales avanzados...")
        spectrum = {
            "violet": self.read_register(0x08),
            "blue": self.read_register(0x0A),
            "green": self.read_register(0x0C),
            "yellow": self.read_register(0x0E),
            "orange": self.read_register(0x10),
            "red": self.read_register(0x12),
        }
        print(f"Espectro avanzado: {spectrum}")
        return spectrum

# # Ejemplo de Uso:

# # Lecturas Calibradas:

# from lib.as7265x import CustomAS7265x

# def main():
#     # Inicializar el sensor
#     sensor = CustomAS7265x(config_path="config/pi1_config.yaml")

#     # Leer espectro calibrado
#     calibrated_data = sensor.read_calibrated_spectrum()
#     print("Datos calibrados:", calibrated_data)

# if __name__ == "__main__":
#     main()


# # Lecturas Avanzadas:
# from lib.as7265x import CustomAS7265x

# def main():
#     sensor = CustomAS7265x(config_path="config/pi1_config.yaml")

#     # Leer datos espectrales avanzados
#     advanced_data = sensor.read_advanced_spectrum()
#     print("Datos avanzados:", advanced_data)

# if __name__ == "__main__":
#     main()
