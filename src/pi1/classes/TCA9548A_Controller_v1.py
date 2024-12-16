from smbus2 import SMBus
import time
import sys
import logging
from qwiic_tca9548a import QwiicTCA9548A

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
        self.address = address
        self.mux = QwiicTCA9548A(address)
        self.i2c_bus = SMBus(1) if i2c_bus is None else i2c_bus

        if not self.mux.is_connected():
            raise ConnectionError(f"[CONTROLLER] [MUX] No se pudo conectar al MUX en la dirección {hex(address)}.")
        logging.info(f"[CONTROLLER] [MUX] TCA9548A conectado correctamente {hex(address)}.")
        
        self.active_channels = set()

    def enable_channel(self, channel):
        try:
            if not self.mux.is_connected():
                raise ConnectionError("[CONTROLLER] [MUX] El MUX TCA9548A no está conectado.")
            if channel not in CHANNELS:
                raise ValueError("[CONTROLLER] [MUX] Entries must be in range of available channels (0-7).")

            self.mux.enable_channels([channel])
            logging.info(f"[CONTROLLER] [MUX] Canal {channel} habilitado correctamente.")
            return True
        except Exception as e:
            logging.error(f"[CONTROLLER] [MUX] No se pudo habilitar el canal {channel}: {e}")
            return False

    def disable_channel(self, channel):
        """
        Deshabilita un canal específico en el MUX.
        :param channel: Canal a deshabilitar.
        """
        if 0 <= channel <= 7:
            self.i2c_bus.write_byte_data(self.address, 0x00, 0x00)  # Apaga todos los canales
            logging.info(f"[CONTROLLER] [MUX] Canal {channel} deshabilitado.")
        else:
            raise ValueError(f"[CONTROLLER] [MUX] Canal {channel} fuera del rango permitido (0-7).")

    def disable_all_channels(self):
        """
        Deshabilita todos los canales del MUX.
        """
        try:
            self.i2c_bus.write_byte_data(self.address, 0x00, 0x00)  # Apaga todos los canales
            logging.info("[CONTROLLER] [MUX] Todos los canales deshabilitados.")
        except Exception as e:
            logging.error(f"[CONTROLLER] [MUX] Error al deshabilitar todos los canales: {e}")
            raise

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
