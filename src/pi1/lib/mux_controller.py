import smbus

class MUXController:
    def __init__(self, i2c_bus=1, i2c_address=0x70):
        """
        Inicializa el controlador del MUX.

        :param i2c_bus: Número del bus I2C donde está conectado el MUX.
        :param i2c_address: Dirección I2C del MUX.
        """
        self.bus = smbus.SMBus(i2c_bus)
        self.i2c_address = i2c_address

    def select_channel(self, channel):
        """
        Selecciona un canal en el MUX para habilitar la comunicación con el dispositivo conectado.

        :param channel: Canal a seleccionar (0-7).
        """
        if channel < 0 or channel > 7:
            raise ValueError("Channel must be between 0 and 7.")
        
        try:
            print(f"Selecting channel {channel} on MUX at address {hex(self.i2c_address)}...")
            self.bus.write_byte(self.i2c_address, 1 << channel)
            print(f"Channel {channel} selected.")
        except Exception as e:
            print(f"Failed to select channel {channel}: {e}")

    def disable_all_channels(self):
        """
        Deshabilita todos los canales del MUX.
        """
        try:
            print(f"Disabling all channels on MUX at address {hex(self.i2c_address)}...")
            self.bus.write_byte(self.i2c_address, 0x00)
            print("All channels disabled.")
        except Exception as e:
            print(f"Failed to disable all channels: {e}")


# # Ejemplo de Uso, si se desea leer datos del primer sensor conectado al canal 0 del MUX.

# from lib.mux_controller import MUXController
# from lib.as7265x import AS7265x

# # Inicializar el MUX y el sensor
# mux = MUXController(i2c_bus=1, i2c_address=0x70)
# sensor = AS7265x(i2c_bus=1)

# # Seleccionar el canal 0 en el MUX
# mux.select_channel(0)

# # Configurar y leer datos del sensor en el canal 0
# sensor.set_device_address(0x49)  # Dirección I2C del sensor en el canal seleccionado
# sensor.configure_sensor()
# spectral_data = sensor.read_spectrum()

# # Deshabilitar todos los canales después de la operación
# mux.disable_all_channels()
