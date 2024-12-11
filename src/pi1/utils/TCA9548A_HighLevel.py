# TCA9548A High Level - Clase de alto nivel para el MUX TCA9548A.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024

import logging
from classes.TCA9548A_Manager import TCA9548AManager

# Configurar logging para el manejo de nivel alto
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')

class TCA9548AMUXHighLevel:
    """
    Manejo de alto nivel para el MUX TCA9548A.
    Este archivo abstrae las operaciones comunes como habilitar/deshabilitar canales.
    """

    def __init__(self, address=0x70):
        """
        Inicializa el controlador de alto nivel para el MUX TCA9548A.
        :param address: Dirección I²C del MUX.
        """
        self.mux = TCA9548AManager(address=address)
        logging.info(f"MUX TCA9548A inicializado en la dirección {hex(address)}.")

    def enable_channel(self, channel):
        """
        Habilita un canal específico en el MUX.
        :param channel: Canal a habilitar (0-7).
        """
        self.mux.enable_channel(channel)
        logging.info(f"Canal {channel} habilitado.")

    def disable_channel(self, channel):
        """
        Deshabilita un canal específico en el MUX.
        :param channel: Canal a deshabilitar (0-7).
        """
        self.mux.disable_channel(channel)
        logging.info(f"Canal {channel} deshabilitado.")

    def enable_multiple_channels(self, channels):
        """
        Habilita múltiples canales en el MUX.
        :param channels: Lista de canales a habilitar (0-7).
        """
        self.mux.enable_multiple_channels(channels)
        logging.info(f"Canales {channels} habilitados.")

    def disable_all_channels(self):
        """
        Deshabilita todos los canales del MUX.
        """
        self.mux.disable_all_channels()
        logging.info("Todos los canales del MUX deshabilitados.")

    def get_active_channel(self):
        """
        Devuelve los canales actualmente activos en el MUX.
        """
        active_channels = self.mux.get_active_channels()
        logging.info(f"Canales activos en el MUX: {active_channels}")
        return active_channels

    def read_control_register(self):
        """
        Lee el registro de control del MUX para determinar los canales activos.
        :return: Byte que representa el estado de los canales activos.
        """
        return self.mux._i2c.read_byte(self.mux.address)

