import smbus
import time


class AS7265x:
    """
    Clase para interactuar con el sensor AS7265x para lecturas espectroscópicas.
    """
    def __init__(self, i2c_bus, i2c_address=0x49, integration_time=100, gain=64):
        """
        Inicializa el sensor AS7265x.

        :param i2c_bus: Número del bus I2C.
        :param i2c_address: Dirección I2C del sensor AS7265x.
        :param integration_time: Tiempo de integración en ms.
        :param gain: Ganancia para las lecturas del sensor.
        """
        self.i2c_address = i2c_address
        self.integration_time = integration_time
        self.gain = gain
        self.bus = smbus.SMBus(i2c_bus)

        # Configurar el sensor
        self.configure_sensor()

    def configure_sensor(self):
        """
        Configura el sensor AS7265x con el tiempo de integración y ganancia especificados.
        """
        print(f"Configurando el sensor AS7265x en la dirección {hex(self.i2c_address)}...")
        self.write_register(0x04, self.integration_time // 2.8)     # Tiempo de integración
        self.write_register(0x05, self.gain)                        # Ganancia
        print("Configuración del sensor completada.")

    def write_register(self, register, value):
        """
        Escribe un valor en un registro del sensor.

        :param register: Registro a escribir.
        :param value: Valor a escribir.
        """
        print(f"Escribiendo valor {value} en el registro {hex(register)}...")
        self.bus.write_byte_data(self.i2c_address, register, value)

    def read_spectrum(self):
        """
        Lee los datos espectroscópicos del sensor.

        :return: Diccionario con las lecturas de los espectros (violeta, azul, verde, amarillo, naranja, rojo).
        """
        print("Leyendo datos espectroscópicos del sensor AS7265x...")
        spectrum = {
            "violet": self.read_register(0x08),
            "blue": self.read_register(0x0A),
            "green": self.read_register(0x0C),
            "yellow": self.read_register(0x0E),
            "orange": self.read_register(0x10),
            "red": self.read_register(0x12),
        }
        print(f"Espectro leído: {spectrum}")
        return spectrum

    def read_register(self, register):
        """
        Lee un valor de un registro del sensor.

        :param register: Registro a leer.
        :return: Valor leído.
        """
        value = self.bus.read_byte_data(self.i2c_address, register)
        print(f"Valor leído del registro {hex(register)}: {value}")
        return value
