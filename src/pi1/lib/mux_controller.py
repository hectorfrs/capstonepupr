import yaml
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

        # Inicializar el MUX
        self.mux = QwiicTCA9548A(address=self.i2c_address)
        if not self.mux.connected:
            raise ConnectionError(f"El MUX con dirección {hex(self.i2c_address)} no está conectado.")
        print(f"MUX conectado en la dirección {hex(self.i2c_address)}.")

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

    # def disable_all_channels(self):
    #     """
    #     Desactiva todos los canales del MUX, escribiendo 0x00 en el registro de con control.
    #     """
    #     try:
    #         #self.mux.disable_all_channels()
    #         self.mux._i2c.writeByte(self.i2c_address, 0x00)  # Dirección, valor
    #         print("Todos los canales desactivados en el MUX.")
    #     except Exception as e:
    #         print(f"Error al desactivar los canales: {e}")
    #         raise

    def disable_all_channels(self):
        """
        Desactiva todos los canales del MUX utilizando smbus.
        """
        try:
            bus = smbus.SMBus(self.i2c_bus)
            bus.write_byte(self.i2c_address, 0x00)
            print("Todos los canales desactivados en el MUX (smbus).")
        except Exception as e:
            print(f"Error al desactivar todos los canales del MUX: {e}")
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



# # Ejemplo de Uso:

# from lib.mux_controller import MUXController

# def main():
#     # Inicializar el controlador del MUX
#     mux = MUXController(i2c_bus=1, i2c_address=0x70)

#     # Validar conexión
#     mux.validate_connection()

#     # Activar canal 0
#     mux.select_channel(0)

#     # Desactivar todos los canales
#     mux.disable_all_channels()

# if __name__ == "__main__":
#     main()


# #Integración con Sensores

# #Este módulo está diseñado para integrarse perfectamente con as7265x.py y el sistema principal.

# from lib.mux_controller import MUXController
# from lib.as7265x import CustomAS7265x

# def main():
#     # Configuración
#     mux = MUXController(i2c_bus=1, i2c_address=0x70)
#     sensor = CustomAS7265x(config_path="config/pi1_config.yaml")

#     # Leer datos del sensor en canal 0
#     mux.select_channel(0)
#     spectral_data = sensor.read_calibrated_spectrum()
#     print("Datos espectrales:", spectral_data)

#     # Desactivar todos los canales
#     mux.disable_all_channels()

# if __name__ == "__main__":
#     main()
