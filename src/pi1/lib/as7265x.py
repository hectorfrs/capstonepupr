import smbus
import time

class AS7265x:
    def __init__(self, i2c_bus=1, integration_time=100, gain=64):
        """
        Inicializa el sensor AS7265x.

        :param i2c_bus: Número del bus I2C donde está conectado el sensor.
        :param integration_time: Tiempo de integración en ms para cada lectura.
        :param gain: Ganancia configurada para el sensor.
        """
        self.bus = smbus.SMBus(i2c_bus)
        self.integration_time = integration_time
        self.gain = gain
        self.device_address = None  # Dirección I2C del sensor asignada dinámicamente

    def set_device_address(self, address):
        """
        Establece la dirección I2C del sensor.
        
        :param address: Dirección I2C del sensor.
        """
        self.device_address = address

    def write_register(self, address, value):
        """
        Escribe un valor en un registro específico del sensor.

        :param address: Dirección del registro.
        :param value: Valor a escribir.
        """
        if self.device_address is None:
            raise ValueError("Device address not set.")
        try:
            self.bus.write_byte_data(self.device_address, address, value)
        except Exception as e:
            print(f"Failed to write to register {address}: {e}")

    def read_register(self, address):
        """
        Lee el valor de un registro específico del sensor.

        :param address: Dirección del registro.
        :return: Valor leído.
        """
        if self.device_address is None:
            raise ValueError("Device address not set.")
        try:
            return self.bus.read_byte_data(self.device_address, address)
        except Exception as e:
            print(f"Failed to read from register {address}: {e}")
            return None

    def configure_sensor(self):
        """
        Configura el sensor con tiempo de integración y ganancia.
        """
        print(f"Configuring AS7265x with integration time {self.integration_time}ms and gain {self.gain}...")
        self.write_register(0x01, self.integration_time)  # Registro de tiempo de integración
        self.write_register(0x02, self.gain)              # Registro de ganancia
        time.sleep(1)

    def update_settings(self, integration_time=None, gain=None):
        """
        Actualiza las configuraciones del sensor de forma dinámica.

        :param integration_time: Nuevo tiempo de integración en ms.
        :param gain: Nueva ganancia.
        """
        if integration_time is not None:
            print(f"Updating integration time to {integration_time}ms...")
            self.integration_time = integration_time
            self.write_register(0x01, integration_time)
        if gain is not None:
            print(f"Updating gain to {gain}...")
            self.gain = gain
            self.write_register(0x02, gain)
        print("Sensor settings updated.")

    def read_spectrum(self):
        """
        Lee los valores espectrales del sensor.

        :return: Diccionario con los valores espectrales.
        """
        print("Reading spectral data from AS7265x...")
        try:
            spectral_data = {
                "violet": self.read_register(0x08),  # Ejemplo: valores del espectro violeta
                "blue": self.read_register(0x0A),   # Ejemplo: valores del espectro azul
                "green": self.read_register(0x0C),  # Ejemplo: valores del espectro verde
                "yellow": self.read_register(0x0E), # Ejemplo: valores del espectro amarillo
                "orange": self.read_register(0x10), # Ejemplo: valores del espectro naranja
                "red": self.read_register(0x12)    # Ejemplo: valores del espectro rojo
            }
            print(f"Spectral data: {spectral_data}")
            return spectral_data
        except Exception as e:
            print(f"Failed to read spectral data: {e}")
            return None
