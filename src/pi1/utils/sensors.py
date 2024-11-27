import smbus


class PressureSensor:
    """
    Clase para manejar sensores de presión.
    """
    def __init__(self, i2c_address, i2c_bus=1, min_pressure=0.0, max_pressure=25.0):
        """
        Inicializa el sensor de presión.

        :param i2c_address: Dirección I2C del sensor.
        :param i2c_bus: Número del bus I2C.
        :param min_pressure: Presión mínima en PSI.
        :param max_pressure: Presión máxima en PSI.
        """
        self.i2c_address = i2c_address
        self.min_pressure = min_pressure
        self.max_pressure = max_pressure
        self.bus = smbus.SMBus(i2c_bus)

    def read_pressure(self):
        """
        Lee la presión desde el sensor.

        :return: Valor de presión en PSI.
        """
        print(f"Leyendo presión desde el sensor en dirección {hex(self.i2c_address)}...")
        raw_data = self.bus.read_word_data(self.i2c_address, 0x00)
        pressure = self._convert_raw_to_pressure(raw_data)
        print(f"Presión leída: {pressure} PSI")
        return pressure

    def _convert_raw_to_pressure(self, raw_data):
        """
        Convierte los datos crudos en presión en PSI.

        :param raw_data: Datos crudos leídos desde el sensor.
        :return: Presión en PSI.
        """
        return self.min_pressure + (raw_data / 65535.0) * (self.max_pressure - self.min_pressure)
