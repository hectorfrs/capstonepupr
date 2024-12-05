import yaml
from smbus2 import SMBus
from qwiic_tca9548a import QwiicTCA9548A

class MUXController:
    """
    Clase para controlar el MUX Qwiic TCA9548A.
    """

    def __init__(self, i2c_bus, i2c_address):
        """
        Inicializa el controlador del MUX.

        :param i2c_bus: Bus I2C donde está conectado el MUX.
        :param i2c_address: Dirección I2C del MUX.
        """
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.bus = SMBus(i2c_bus)  # Inicializar el bus I2C

        # Inicializar el MUX
        self.mux = QwiicTCA9548A(address=self.i2c_address)
        if not self.mux.connected:
            raise ConnectionError(f"El MUX con dirección {hex(self.i2c_address)} no está conectado.")
        print(f"MUX conectado en la dirección {hex(self.i2c_address)}.")

    def write_register(self, register, value):
        """
        Escribe un valor en un registro del sensor a través del bus I2C.
        """
        try:
            self.bus.write_byte_data(self.i2c_address, register, value)
        except OSError as e:
            print(f"Error al escribir en el registro {hex(register)} del dispositivo {hex(self.i2c_address)}: {e}")
            raise

    @staticmethod
    def is_sensor_connected(bus, address):
        """
        Verifica si hay un dispositivo en la dirección I2C especificada.
        """
        try:
            bus.read_byte(address)
            return True
        except OSError:
            return False

    def select_channel(self, channel):
        """
        Activa un canal específico en el MUX.

        :param channel: Número del canal a activar (0-7).
        """
        if channel < 0 or channel > 7:
            raise ValueError("El canal debe estar entre 0 y 7.")

        try:
            self.mux.enable_channels(1 << channel)
            print(f"Canal {channel} activado en el MUX.")
        except Exception as e:
            print(f"Error al activar el canal {channel}: {e}")
            raise

    def disable_all_channels(self):
        """
        Desactiva todos los canales del MUX.
        """
        try:
            self.mux.enable_channels(0)
            print("Todos los canales desactivados en el MUX.")
        except Exception as e:
            print(f"Error al desactivar los canales: {e}")
            raise

    def validate_connection(self):
        """
        Valida si el MUX está conectado y funcionando correctamente.
        """
        if not self.mux.connected:
            raise ConnectionError(f"El MUX con dirección {hex(self.i2c_address)} ha perdido la conexión.")
        print("Conexión al MUX validada.")

    def reset_channel(self, channel):
        """
        Resetea un canal específico en el MUX desactivando todos los canales
        y volviendo a activar solo el canal deseado.

        :param channel: Número del canal a resetear (0-7).
        """
        if channel < 0 or channel > 7:
            raise ValueError("El canal debe estar entre 0 y 7.")

        try:
            # Desactivar todos los canales
            self.disable_all_channels()
            print(f"Todos los canales desactivados antes de resetear el canal {channel}.")

            # Activar el canal deseado
            self.select_channel(channel)
            print(f"Canal {channel} reseteado y activado.")
        except Exception as e:
            print(f"Error al resetear el canal {channel}: {e}")
            raise