# TCA9548A_Manager.py - Clase para manejar el MUX TCA9548A utilizando la librería Qwiic.
# Desarrollado por Héctor F. Rivera Santiago
# copyright (c) 2024

import qwiic
import qwiic_tca9548a
import smbus2
import time
import logging
import sys

# Configuración de logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class TCA9548AManager:
    """Clase para manejar el MUX TCA9548A utilizando la librería Qwiic."""

    def __init__(self, address=0x70, i2c_bus=1):
        """
        Inicializa el MUX TCA9548A.
        :param address: Dirección I2C del MUX.
        :param i2c_bus: Número del bus I2C (por defecto: 1).
        """
        self.address = address
        self.bus = smbus2.SMBus(i2c_bus)

        try:
            self.bus.read_byte(self.address)
            logging.info(f"MUX TCA9548A conectado en la dirección {hex(self.address)}.")
        except Exception as e:
            logging.error(f"No se puede conectar al MUX en {hex(self.address)}: {e}")
            raise

        if not self.mux.is_connected():
            logging.error(f"No se puede conectar al MUX en la dirección {hex(address)}")
            raise ConnectionError(f"No se puede conectar al MUX en la dirección {hex(address)}")
            logging.info(f"MUX TCA9548A conectado en la dirección {hex(address)}")

    def enable_channel(self, channel):
        """
        Habilita un canal en el MUX.
        :param channel: Canal a habilitar (0-7).
        """
        if not 0 <= channel <= 7:
            raise ValueError("El canal debe estar entre 0 y 7.")
        self.mux.enable_channels(1 << channel)
        logging.info(f"Canal {channel} habilitado.")

    def disable_channel(self, channel):
        """
        Deshabilita un canal en el MUX.
        :param channel: Canal a deshabilitar (0-7).
        """
        if not 0 <= channel <= 7:
            raise ValueError("El canal debe estar entre 0 y 7.")
        self.mux.disable_channels(1 << channel)
        logging.info(f"Canal {channel} deshabilitado.")

    def enable_multiple_channels(self, channels):
        """
        Habilita múltiples canales en el MUX.
        :param channels: Lista de canales a habilitar (0-7).
        """
        mask = 0
        for channel in channels:
            if not isinstance(channel, int) or not 0 <= channel <= 7:
                raise ValueError(f"Canal inválido: {channel}. Debe ser un entero entre 0 y 7.")
            mask |= 1 << channel
        self.mux.enable_channels(mask)
        logging.info(f"Canales {channels} habilitados.")

    def disable_all_channels(self):
        """
        Deshabilita todos los canales del MUX.
        """
        self.mux.disable_all_channels()
        logging.info("Todos los canales deshabilitados.")

    def get_active_channels(self):
        """
        Devuelve los canales actualmente activos en el MUX.
        :return: Lista de canales activos (0-7).
        """
        status = self.read_control_register()
        active_channels = [i for i in range(8) if status & (1 << i)]
        logging.info(f"Canales activos: {active_channels}")
        return active_channels

    def read_control_register(self):
        """
        Lee el registro de control del MUX para determinar los canales activos.
        :return: Byte que representa el estado de los canales activos.
        """
        try:
            status = self.bus.read_byte(self.address)  # Dirección del MUX
            logging.info(f"Registro de control leído: {bin(status)}")
            return status
        except Exception as e:
            logging.error(f"Error al leer el registro de control del MUX: {e}")
            raise

    def reset(self):
        """
        Resetea el MUX a través del comando de reset.
        """
        self.mux.disable_all_channels()
        logging.info("MUX reseteado y todos los canales deshabilitados.")
