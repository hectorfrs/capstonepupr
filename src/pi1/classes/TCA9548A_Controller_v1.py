from smbus2 import SMBus
import time
import sys
import logging
import qwiic_tca9548a

# Configuración de logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Dirección del MUX
MUX_ADDRESS = 0x70

# Canales del MUX
CHANNELS = {
    0: 0x01,  # Canal 0
    1: 0x02,  # Canal 1
    2: 0x04,  # Canal 2
    3: 0x08,  # Canal 3
    4: 0x10,  # Canal 4
    5: 0x20,  # Canal 5
    6: 0x40,  # Canal 6
    7: 0x80,  # Canal 7
}

class MUX_TCA9548A:

    def __init__(self, i2c_bus=1, address=MUX_ADDRESS):
        """
        Inicializa el controlador del MUX TCA9548A.
        """
        self.i2c_bus = i2c_bus
        self.address = address
        self.mux = qwiic_tca9548a.QwiicTCA9548A()
        if not self.mux.connected:
            raise Exception("[CONTROLLER] [MUX] TCA9548A no detectado en el bus I2C.")
        logging.info("[CONTROLLER] [MUX] TCA9548A conectado correctamente.")

    def enable_channel(self, channel):
        """
        Habilita un canal específico del MUX.
        """
        if channel < 0 or channel > 7:
            logging.error(f"Canal {channel} no válido. Seleccione un canal entre 0 y 7.")
            return False
        try:
            self.mux.enable_channels(1 << channel)
            logging.info(f"Canal {channel} habilitado correctamente.")
            return True
        except Exception as e:
            logging.error(f"Error al habilitar canal {channel}: {e}")
            return False
    
    def enable_multiple_channels(self, channels):
        """
        Habilita múltiples canales en el MUX.

        :param channels: Lista de canales a habilitar.
        """
        for channel in channels:
            if not self.mux.enable_channels(channel):
                raise RuntimeError(f"[CONTROLLER] [MUX] No se pudo habilitar el canal {channel}.")

    def disable_all_channels(self):
        """
        Deshabilita todos los canales del MUX.
        """
        try:
            self.mux.disable_channels(0xFF)
            logging.info("Todos los canales deshabilitados.")
        except Exception as e:
            logging.error(f"Error al deshabilitar los canales: {e}")

    def scan_channels(self):
        """
        Escanea todos los canales del MUX y registra dispositivos detectados.
        """
        logging.info("Escaneando todos los canales del MUX...")
        devices = {}
        for channel in range(8):
            self.enable_channel(channel)
            time.sleep(0.1)  # Esperar para estabilizar el canal
            detected = self.scan_i2c_bus()
            devices[channel] = detected
            logging.info(f"Canal {channel}: {detected}")
        self.disable_all_channels()
        return devices

    def scan_i2c_bus(self):
        """
        Escanea el bus I2C en el canal activo y retorna direcciones detectadas.
        """
        detected_devices = []
        try:
            for address in range(0x03, 0x77):
                if self.mux.is_device_present(address):
                    detected_devices.append(hex(address))
        except Exception as e:
            logging.error(f"Error al escanear el bus I2C: {e}")
        return detected_devices

# ------------------- Ejemplo de Uso -------------------
# if __name__ == "__main__":
#     try:
#         mux = TCA9548AController()

#         # Escanear todos los canales y dispositivos conectados
#         devices = mux.scan_channels()
#         logging.info(f"Dispositivos detectados por canal: {devices}")

#         # Habilitar canal 0 y realizar una prueba
#         if mux.enable_channel(0):
#             logging.info("Canal 0 habilitado correctamente.")
#             time.sleep(1)

#         # Deshabilitar todos los canales
#         mux.disable_all_channels()

#     except Exception as e:
#         logging.error(f"Error durante la inicialización o uso del MUX: {e}")
